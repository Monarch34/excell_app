import { mount } from '@vue/test-utils';
import { defineComponent, ref } from 'vue';
import { describe, expect, it } from 'vitest';
import ColumnMatchingGroupsPanel from './ColumnMatchingGroupsPanel.vue';
import type { MatchingColumnGroup } from '@/types/domain';

const AppFieldStub = defineComponent({
  inheritAttrs: false,
  props: {
    error: {
      type: String,
      default: undefined,
    },
  },
  template: `
    <div class="app-field-stub" :class="$attrs.class">
      <slot />
      <small v-if="error" class="app-field-error">{{ error }}</small>
    </div>
  `,
});

const InputTextStub = defineComponent({
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    id: {
      type: String,
      default: undefined,
    },
    placeholder: {
      type: String,
      default: undefined,
    },
  },
  emits: ['update:modelValue', 'blur'],
  template: `
    <input
      class="input-text-stub"
      :id="id"
      :placeholder="placeholder"
      :value="modelValue ?? ''"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
    />
  `,
});

const ColumnMatchingGroupsHarness = defineComponent({
  components: { ColumnMatchingGroupsPanel },
  setup() {
    const groups = ref<MatchingColumnGroup[]>([
      { id: 'g1', name: 'Group 1', color: '#60A5FA', columns: [] },
    ]);

    function handleUpdateGroup(groupId: string, patch: { name?: string; color?: string }) {
      const group = groups.value.find((value) => value.id === groupId);
      if (!group) return;
      if (typeof patch.name === 'string') group.name = patch.name.trim() || group.name;
      if (typeof patch.color === 'string') group.color = patch.color;
    }

    return {
      groups,
      handleUpdateGroup,
    };
  },
  template: `
    <ColumnMatchingGroupsPanel
      :columns="[{ name: 'Load', selected: true }, { name: 'Extension', selected: true }]"
      :groups="groups"
      @createGroup="$emit('createGroup')"
      @deleteGroup="$emit('deleteGroup', $event)"
      @updateGroup="handleUpdateGroup"
      @setGroupColumns="$emit('setGroupColumns', $event)"
    />
  `,
});

describe('ColumnMatchingGroupsPanel', () => {
  it('keeps a local required-name error until the group name becomes valid', async () => {
    const wrapper = mount(ColumnMatchingGroupsHarness, {
      global: {
        stubs: {
          AppField: AppFieldStub,
          InputText: InputTextStub,
          MultiSelect: true,
          Button: true,
          Tag: true,
        },
      },
    });

    const nameInput = wrapper.get('#match-group-name-g1');

    await nameInput.setValue('');
    await nameInput.trigger('blur');
    expect(wrapper.text()).toContain('Group name is required');

    await nameInput.setValue('Geometry');
    expect(wrapper.text()).not.toContain('Group name is required');

    expect(wrapper.getComponent(ColumnMatchingGroupsPanel).emitted('updateGroup')).toEqual([
      ['g1', { name: 'Geometry' }],
    ]);
  });
});
