import { describe, it, expect } from 'vitest'
import { filterRowsForChartBaseline } from './chartBaselineFilter'

describe('filterRowsForChartBaseline', () => {
  const sampleRows = [
    { x: 1, y1: 10, y2: 20 },
    { x: 2, y1: 15, y2: 25 },
    { x: 3, y1: 20, y2: 30 },
    { x: 4, y1: 25, y2: 35 },
    { x: 5, y1: 30, y2: 40 }
  ]

  it('should return all rows when no baseline filters are defined', () => {
    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(sampleRows, chart)
    expect(result).toEqual(sampleRows)
  })

  it('should return all rows without baseline region selection', () => {
    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(sampleRows, chart)
    expect(result).toHaveLength(5)
    expect(result[0].x).toBe(1)
    expect(result[4].x).toBe(5)
  })

  it('should keep rows when no area filter mode is set', () => {
    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(sampleRows, chart)
    expect(result).toHaveLength(5)
    expect(result[0].x).toBe(1)
    expect(result[4].x).toBe(5)
  })

  it('should keep rows when areaSpec is null', () => {
    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(sampleRows, chart)
    expect(result).toHaveLength(5)
    expect(result.map(r => r.x)).toEqual([1, 2, 3, 4, 5])
  })

  it('should include all valid rows by default', () => {
    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(sampleRows, chart)
    expect(result).toHaveLength(5)
    expect(result.map(r => r.x)).toEqual([1, 2, 3, 4, 5])
  })

  it('should keep default ordering when unfiltered', () => {
    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(sampleRows, chart)
    expect(result).toHaveLength(5)
    expect(result.map(r => r.x)).toEqual([1, 2, 3, 4, 5])
  })

  it('should exclude rows with NaN x values', () => {
    const rowsWithNaN = [
      { x: 1, y1: 10, y2: 20 },
      { x: 'invalid', y1: 15, y2: 25 },
      { x: 3, y1: 20, y2: 30 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(rowsWithNaN, chart)
    expect(result).toHaveLength(2)
    expect(result.map(r => r.x)).toEqual([1, 3])
  })

  it('should exclude rows with NaN y values', () => {
    const rowsWithNaN = [
      { x: 1, y1: 10, y2: 20 },
      { x: 2, y1: 'invalid', y2: 25 },
      { x: 3, y1: 20, y2: 30 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(rowsWithNaN, chart)
    expect(result).toHaveLength(2)
    expect(result.map(r => r.x)).toEqual([1, 3])
  })

  it('should filter positive area mode correctly', () => {
    const rows = [
      { x: 1, y1: 10, y2: 20 },
      { x: 2, y1: -5, y2: 25 },
      { x: 3, y1: 20, y2: 30 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: {
        mode: 'positive' as const,
        baseline: 0,
        baselineAxis: 'y' as const,
        xColumn: 'x',
        yColumn: 'y1'
      }
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(2)
    expect(result.map(r => r.x)).toEqual([1, 3])
  })

  it('should filter negative area mode correctly', () => {
    const rows = [
      { x: 1, y1: -10, y2: -20 },
      { x: 2, y1: 5, y2: -25 },
      { x: 3, y1: -20, y2: -30 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: {
        mode: 'negative' as const,
        baseline: 0,
        baselineAxis: 'y' as const,
        xColumn: 'x',
        yColumn: 'y1'
      }
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(2)
    expect(result.map(r => r.x)).toEqual([1, 3])
  })

  it('should include all rows in total area mode', () => {
    const rows = [
      { x: 1, y1: -10, y2: 20 },
      { x: 2, y1: 5, y2: -25 },
      { x: 3, y1: -20, y2: 30 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: {
        mode: 'total' as const,
        baseline: 0,
        baselineAxis: 'y' as const,
        xColumn: 'x',
        yColumn: 'y1'
      }
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(3)
  })

  it('should handle x-axis baseline for positive area mode', () => {
    const rows = [
      { x: 1, y1: 10, y2: 20 },
      { x: 2, y1: 15, y2: 25 },
      { x: 3, y1: 20, y2: 30 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: {
        mode: 'positive' as const,
        baseline: 2,
        baselineAxis: 'x' as const,
        xColumn: 'x',
        yColumn: 'y1'
      }
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(2)
    expect(result.map(r => r.x)).toEqual([2, 3])
  })

  it('should apply area filters correctly', () => {
    const rows = [
      { x: 1, y1: 10, y2: 20 },
      { x: 2, y1: -5, y2: 25 },
      { x: 3, y1: 20, y2: 30 },
      { x: 4, y1: 25, y2: 35 },
      { x: 5, y1: 30, y2: 40 }
    ]

    const chart = {
      chartType: 'area' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: {
        mode: 'positive' as const,
        baseline: 0,
        baselineAxis: 'y' as const,
        xColumn: 'x',
        yColumn: 'y1'
      }
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(4)
    expect(result.map(r => r.x)).toEqual([1, 3, 4, 5])
  })

  it('should ignore areaSpec filters for non-area chart types', () => {
    const rows = [
      { x: 1, y1: -10, y2: -20 },
      { x: 2, y1: 5, y2: -25 },
      { x: 3, y1: -20, y2: -30 }
    ]

    const chart = {
      chartType: 'line' as const,
      xColumn: 'x',
      yColumns: ['y1', 'y2'],
      areaSpec: {
        mode: 'positive' as const,
        baseline: 0,
        baselineAxis: 'y' as const,
        xColumn: 'x',
        yColumn: 'y1'
      }
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(3)
  })

  it('should apply baseline regions for line charts', () => {
    const rows = [
      { x: -1, y1: 2 },
      { x: 1, y1: 2 },
      { x: 1, y1: -2 },
      { x: -1, y1: -2 }
    ]

    const chart = {
      chartType: 'line' as const,
      xColumn: 'x',
      yColumns: ['y1'],
      baselineSpec: {
        xBaseline: 0,
        yBaseline: 0,
        regions: ['top-right' as const]
      },
      areaSpec: null
    }

    const result = filterRowsForChartBaseline(rows, chart)
    expect(result).toHaveLength(1)
    expect(result[0].x).toBe(1)
    expect(result[0].y1).toBe(2)
  })
})


