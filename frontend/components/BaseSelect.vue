<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";

interface SelectOption {
  value: unknown;
  label: string;
  disabled?: boolean;
}

const props = withDefaults(
  defineProps<{
    modelValue: unknown;
    options: SelectOption[];
    placeholder?: string;
    disabled?: boolean;
    size?: "sm" | "md";
    variant?: "default" | "pill";
    triggerClass?: string;
  }>(),
  {
    placeholder: "Seleccionar…",
    disabled: false,
    size: "md",
    variant: "default",
    triggerClass: "",
  },
);

const emit = defineEmits<{
  (e: "update:modelValue", value: unknown): void;
  (e: "change", value: unknown): void;
}>();

const open = ref(false);
const triggerRef = ref<HTMLButtonElement | null>(null);
const panelRef = ref<HTMLDivElement | null>(null);
const highlighted = ref(-1);

// Position of the floating panel (teleported to body, fixed positioning).
const panelStyle = ref<Record<string, string>>({});
const dropUp = ref(false);

const selectedOption = computed(() =>
  props.options.find((o) => o.value === props.modelValue),
);

const displayLabel = computed(
  () => selectedOption.value?.label ?? props.placeholder,
);

const hasValue = computed(() => selectedOption.value !== undefined);

function updatePosition() {
  const el = triggerRef.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const spaceBelow = window.innerHeight - rect.bottom;
  const estimatedHeight = Math.min(props.options.length * 40 + 10, 280);
  const shouldDropUp = spaceBelow < estimatedHeight + 12 && rect.top > spaceBelow;
  dropUp.value = shouldDropUp;
  panelStyle.value = {
    position: "fixed",
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    ...(shouldDropUp
      ? { bottom: `${window.innerHeight - rect.top + 6}px` }
      : { top: `${rect.bottom + 6}px` }),
  };
}

function openMenu() {
  if (props.disabled) return;
  updatePosition();
  open.value = true;
  highlighted.value = props.options.findIndex(
    (o) => o.value === props.modelValue,
  );
  nextTick(() => {
    scrollHighlightedIntoView();
  });
}

function closeMenu() {
  open.value = false;
  highlighted.value = -1;
}

function toggleMenu() {
  open.value ? closeMenu() : openMenu();
}

function selectOption(opt: SelectOption) {
  if (opt.disabled) return;
  emit("update:modelValue", opt.value);
  emit("change", opt.value);
  closeMenu();
  triggerRef.value?.focus();
}

function scrollHighlightedIntoView() {
  const panel = panelRef.value;
  if (!panel || highlighted.value < 0) return;
  const item = panel.children[highlighted.value] as HTMLElement | undefined;
  item?.scrollIntoView({ block: "nearest" });
}

function moveHighlight(dir: 1 | -1) {
  const total = props.options.length;
  if (!total) return;
  let next = highlighted.value;
  for (let i = 0; i < total; i++) {
    next = (next + dir + total) % total;
    if (!props.options[next]?.disabled) break;
  }
  highlighted.value = next;
  nextTick(scrollHighlightedIntoView);
}

function onTriggerKeydown(e: KeyboardEvent) {
  if (props.disabled) return;
  switch (e.key) {
    case "Enter":
    case " ":
      e.preventDefault();
      open.value ? confirmHighlighted() : openMenu();
      break;
    case "ArrowDown":
      e.preventDefault();
      open.value ? moveHighlight(1) : openMenu();
      break;
    case "ArrowUp":
      e.preventDefault();
      open.value ? moveHighlight(-1) : openMenu();
      break;
    case "Escape":
      if (open.value) {
        e.preventDefault();
        closeMenu();
      }
      break;
    case "Tab":
      closeMenu();
      break;
  }
}

function confirmHighlighted() {
  const opt = props.options[highlighted.value];
  if (opt) selectOption(opt);
}

function onClickOutside(e: MouseEvent) {
  const target = e.target as Node;
  if (
    triggerRef.value?.contains(target) ||
    panelRef.value?.contains(target)
  ) {
    return;
  }
  closeMenu();
}

watch(open, (isOpen) => {
  if (isOpen) {
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);
    document.addEventListener("mousedown", onClickOutside);
  } else {
    window.removeEventListener("scroll", updatePosition, true);
    window.removeEventListener("resize", updatePosition);
    document.removeEventListener("mousedown", onClickOutside);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", updatePosition, true);
  window.removeEventListener("resize", updatePosition);
  document.removeEventListener("mousedown", onClickOutside);
});
</script>

<template>
  <div class="base-select" :class="{ 'base-select--pill': variant === 'pill' }">
    <button
      ref="triggerRef"
      type="button"
      class="base-select__trigger"
      :class="[
        triggerClass,
        {
          'base-select__trigger--open': open,
          'base-select__trigger--placeholder': !hasValue,
          'base-select__trigger--sm': size === 'sm',
          'base-select__trigger--pill': variant === 'pill',
        },
      ]"
      :disabled="disabled"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggleMenu"
      @keydown="onTriggerKeydown"
    >
      <span class="base-select__label">{{ displayLabel }}</span>
      <svg
        class="base-select__chevron"
        :class="{ 'base-select__chevron--open': open }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1.6"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
      </svg>
    </button>

    <Teleport to="body">
      <Transition :name="dropUp ? 'base-select-up' : 'base-select-down'">
        <div
          v-if="open"
          ref="panelRef"
          class="base-select__panel"
          :style="panelStyle"
          role="listbox"
        >
          <button
            v-for="(opt, i) in options"
            :key="i"
            type="button"
            role="option"
            class="base-select__option"
            :class="{
              'base-select__option--active': opt.value === modelValue,
              'base-select__option--highlight': i === highlighted,
              'base-select__option--disabled': opt.disabled,
            }"
            :aria-selected="opt.value === modelValue"
            :disabled="opt.disabled"
            @mouseenter="highlighted = i"
            @click="selectOption(opt)"
          >
            <span class="base-select__option-label">{{ opt.label }}</span>
            <svg
              v-if="opt.value === modelValue"
              class="base-select__check"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2.2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.base-select {
  position: relative;
  width: 100%;
}

.base-select--pill {
  width: auto;
}

.base-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  width: 100%;
  height: 2.75rem;
  padding: 0 0.75rem 0 1rem;
  border-radius: 12px;
  border: 1px solid rgba(210, 210, 215, 0.7);
  background: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
  color: #1d1d1f;
  text-align: left;
  cursor: pointer;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.base-select__trigger:hover:not(:disabled) {
  border-color: #d2d2d7;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.base-select__trigger--open,
.base-select__trigger:focus-visible {
  border-color: rgba(201, 168, 76, 0.6);
  background: #fff;
  box-shadow:
    0 0 0 3px rgba(201, 168, 76, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.04);
}

.base-select__trigger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.base-select__trigger--placeholder {
  color: #86868b;
}

.base-select__trigger--sm {
  height: 2.25rem;
  padding: 0 0.625rem 0 0.75rem;
  font-size: 0.75rem;
  border-color: rgba(210, 210, 215, 0.6);
}

.base-select__trigger--pill {
  width: auto;
  height: auto;
  gap: 0.25rem;
  padding: 0.15rem 0.5rem;
  font-size: 10px;
  font-weight: 500;
  border-radius: 8px;
}
.base-select__trigger--pill:hover:not(:disabled) {
  box-shadow: none;
}
.base-select__trigger--pill .base-select__chevron {
  width: 0.7rem;
  height: 0.7rem;
  color: currentColor;
  opacity: 0.7;
}

.base-select__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.base-select__chevron {
  width: 0.95rem;
  height: 0.95rem;
  flex-shrink: 0;
  color: #86868b;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.base-select__chevron--open {
  transform: rotate(180deg);
  color: #1d1d1f;
}

.base-select__panel {
  z-index: 9999;
  max-height: 280px;
  overflow-y: auto;
  padding: 0.375rem;
  border-radius: 14px;
  border: 1px solid rgba(210, 210, 215, 0.7);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.06),
    0 12px 40px rgba(0, 0, 0, 0.12);
}

.base-select__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.625rem;
  border-radius: 9px;
  font-size: 0.875rem;
  color: #1d1d1f;
  text-align: left;
  cursor: pointer;
  background: transparent;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.base-select__option--highlight {
  background: rgba(201, 168, 76, 0.12);
}

.base-select__option--active {
  color: #a07c30;
  font-weight: 500;
}

.base-select__option--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.base-select__option-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.base-select__check {
  width: 0.95rem;
  height: 0.95rem;
  flex-shrink: 0;
  color: #c9a84c;
}

/* Dropdown animations */
.base-select-down-enter-active,
.base-select-up-enter-active {
  transition:
    opacity 0.18s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}
.base-select-down-leave-active,
.base-select-up-leave-active {
  transition:
    opacity 0.12s ease,
    transform 0.12s ease;
}
.base-select-down-enter-from,
.base-select-down-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}
.base-select-up-enter-from,
.base-select-up-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.97);
}
</style>
