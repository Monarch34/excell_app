"""
Generic Processing Service - orchestrates operations + formula evaluation.

Replaces the domain-coupled EngineService. This service is fully generic:
it receives data + config from the frontend and executes it blindly.
"""

import logging
from typing import Any

import pandas as pd

from src.core.column_mapping import resolve_operation_columns
from src.core.formulas.dependency import CycleError, DerivedColumnDef, resolve_formula_order
from src.core.formulas.engine import FormulaEngine, UserFormula
from src.core.operations import execute_operation
from src.services.formula_context import apply_cut_point, rewrite_formula_references

logger = logging.getLogger(__name__)
ProcessingResultValue = float | int | str | bool | None

# FormulaEngine is stateless — reuse a single instance for the lifetime of the process.
_formula_engine = FormulaEngine()


class ProcessingService:
    """
    Stateless service that processes data through operations and formulas.
    """

    def process(
        self,
        df: pd.DataFrame,
        operations: list[dict[str, Any]],
        formulas: list[UserFormula],
        parameters: dict[str, float],
        column_mapping: dict[str, str] | None = None,
        derived_parameters: list[dict[str, str]] | None = None,
        initial_results: dict[str, ProcessingResultValue] | None = None,
        header_mapping: dict[str, str] | None = None,
    ) -> tuple[pd.DataFrame, dict[str, ProcessingResultValue]]:
        """
        Full processing pipeline:
        1. Initialize results with initial_results (for manual inputs)
        2. Resolve column roles in operations via column_mapping
        3. Execute operations in sequence
        4. Merge operation results into parameters dict
        5. Compute ALL derived items (parameters + columns) together in dependency order
        6. Return processed DataFrame + results
        """
        results: dict[str, ProcessingResultValue] = (
            initial_results.copy() if initial_results else {}
        )
        working_df = df  # caller already copies; avoid redundant allocation

        for i, op in enumerate(operations):
            op_type = op.get("type", "")
            op_config = op.get("config", {})
            resolved_config = resolve_operation_columns(op_config, column_mapping)

            logger.debug(f"Executing operation {i + 1}/{len(operations)}: {op_type}")
            try:
                working_df, results = execute_operation(
                    op_type, working_df, resolved_config, results
                )
            except Exception as e:
                logger.error(f"Operation {i + 1}/{len(operations)} '{op_type}' failed: {e}")
                raise

        merged_params = {**parameters}
        for key, value in results.items():
            if isinstance(value, int | float):
                merged_params[key] = float(value)

        reference_index = results.get("manual_reference_index")

        # Merge derived_parameters and user_formulas into a single list so they
        # can be evaluated in correct dependency order.  Parameters that DON'T
        # reference any column formula can still be computed early; the rest
        # are deferred until after the columns they depend on are materialised.
        all_derived: list[dict[str, str]] = []
        if derived_parameters:
            all_derived.extend(derived_parameters)
        formula_names: set[str] = set()
        if formulas:
            for f in formulas:
                all_derived.append({"name": f.name, "formula": f.formula})
                formula_names.add(f.name)

        if all_derived:
            working_df, merged_params = self._compute_all_derived(
                all_derived,
                merged_params,
                working_df,
                reference_index,
                formula_names,
                header_mapping,
            )

        # Include derived parameter scalars in the response so the frontend
        # can display them.  Only copy keys that were newly computed.
        original_param_keys = set(parameters.keys())
        for key, value in merged_params.items():
            if (
                key not in original_param_keys
                and key not in results
                and isinstance(value, int | float)
            ):
                results[key] = value

        return working_df, results

    def _compute_all_derived(
        self,
        all_derived: list[dict[str, str]],
        params: dict[str, float],
        df: pd.DataFrame,
        reference_index: int | None = None,
        column_formula_names: set[str] | None = None,
        header_mapping: dict[str, str] | None = None,
    ) -> tuple[pd.DataFrame, dict[str, float]]:
        """
        Compute ALL derived items (both scalar parameters and column formulas)
        in proper dependency order.

        Items whose names appear in ``column_formula_names`` are treated as
        column-level formulas and applied through ``apply_cut_point`` (values
        before the reference row are filled with NaN).  Everything else is
        evaluated as a scalar parameter.
        """
        column_formula_names = column_formula_names or set()
        result = dict(params)
        working_df = df.copy()
        formula_engine = _formula_engine

        if working_df.empty:
            for item in all_derived:
                name = item.get("name", "")
                if name and name in column_formula_names:
                    working_df[name] = pd.Series(dtype=float)
            return working_df, result

        if len(all_derived) > FormulaEngine.MAX_FORMULAS:
            raise ValueError(
                f"Too many derived items: {len(all_derived)}. Maximum is {FormulaEngine.MAX_FORMULAS}"
            )

        # Resolve dependency order across ALL items
        derived_defs = []
        rewritten_formulas_by_name: dict[str, str] = {}
        available_derived_names = [item.get("name") for item in all_derived if item.get("name")]
        for item in all_derived:
            name = item.get("name", "")
            raw_formula = item.get("formula", "")
            if not name or not raw_formula:
                continue

            # Rewrite formula dynamically using currently available columns and params
            # BEFORE resolving dependencies, otherwise aliases aren't accounted for
            rewritten_formula = rewrite_formula_references(
                raw_formula,
                available_columns=working_df.columns.tolist() + available_derived_names,
                available_parameters=list(result.keys()),
                header_mapping=header_mapping or {},
            )
            rewritten_formulas_by_name[name] = rewritten_formula

            derived_defs.append(
                DerivedColumnDef(
                    id=name,
                    name=name,
                    formula=rewritten_formula,
                    enabled=True,
                )
            )

        try:
            ordered = resolve_formula_order(
                derived_columns=derived_defs,
                available_originals=working_df.columns.tolist(),
                parameters=list(result.keys()) if result else [],
            )
        except CycleError as exc:
            raise ValueError(str(exc)) from exc

        ref_int = reference_index if isinstance(reference_index, int) else None

        for item in ordered:
            try:
                rewritten_formula = rewritten_formulas_by_name.get(item.name, item.formula)

                if item.name in column_formula_names:
                    # Column formula → apply via cut point (NaN before ref row)
                    user_formula = UserFormula(
                        name=item.name,
                        formula=rewritten_formula,
                    )
                    working_df = apply_cut_point(
                        working_df,
                        [user_formula],
                        result,
                        ref_int,
                        formula_engine=formula_engine,
                    )
                    logger.debug(f"Applied column formula: {item.name}")
                else:
                    # Scalar parameter
                    eval_result = formula_engine.evaluate(
                        rewritten_formula,
                        working_df,
                        parameters=result,
                        reference_index=ref_int,
                    )
                    if isinstance(eval_result, int | float):
                        result[item.name] = float(eval_result)
                        logger.debug(f"Computed derived parameter: {item.name} = {eval_result}")
                    else:
                        # Formula produced a vector – materialise as column
                        working_df[item.name] = eval_result
                        logger.warning(f"Parameter-type formula '{item.name}' produced a vector; materialised as column")
            except Exception as e:
                raise ValueError(f"Failed to compute derived item '{item.name}': {e}") from e

        return working_df, result


# Singleton instance
processing_service = ProcessingService()
