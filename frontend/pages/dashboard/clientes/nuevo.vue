<script setup lang="ts">
import { useClientsStore } from "~/stores/clients";

definePageMeta({ middleware: ["auth", "role"] });

const store = useClientsStore();
const router = useRouter();

onMounted(() => store.fetchTypes());

const form = reactive({
  nombre_cliente: "",
  tipo_cliente: "" as string | number,
  nombre_facturacion: "",
  cif: "",
  email_facturacion: "",
  direccion_facturacion: "",
  codigo_postal: "",
  ciudad: "",
  pais: "España",
  contrato_firmado: false,
});

const contratoFile = ref<File | null>(null);
const isLoading = ref(false);
const errors = ref<Record<string, string>>({});

function handleFile(e: Event) {
  const input = e.target as HTMLInputElement;
  contratoFile.value = input.files?.[0] ?? null;
}

async function handleSubmit() {
  errors.value = {};
  isLoading.value = true;

  try {
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (v !== "" && v !== null && v !== undefined) {
        fd.append(k, String(v));
      }
    });
    if (contratoFile.value) fd.append("contrato", contratoFile.value);

    await store.create(fd);
    await router.push("/dashboard/clientes");
  } catch (err: unknown) {
    const e = err as { data?: Record<string, string[]> };
    if (e?.data) {
      Object.entries(e.data).forEach(([field, msgs]) => {
        errors.value[field] = Array.isArray(msgs) ? msgs[0] : String(msgs);
      });
    } else {
      errors.value.general = "Error al crear el cliente. Inténtalo de nuevo.";
    }
  } finally {
    isLoading.value = false;
  }
}

const SECTIONS = [
  { id: "identificacion", label: "Identificación" },
  { id: "facturacion", label: "Facturación" },
  { id: "contrato", label: "Contrato" },
];

const activeSection = ref("identificacion");
</script>

<template>
  <div class="max-w-2xl animate-fade-up">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-7">
      <NuxtLink
        to="/dashboard/clientes"
        class="flex items-center gap-1.5 text-xs text-muted hover:text-ink transition-colors"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Clientes
      </NuxtLink>
      <span class="text-border">/</span>
      <span class="text-xs text-ink">Nuevo cliente</span>
    </div>

    <div class="mb-6">
      <p class="text-xs font-medium uppercase tracking-widest text-gold/60 mb-0.5">Alta</p>
      <h1 class="text-3xl font-semibold tracking-tight text-ink">Nuevo cliente</h1>
    </div>

    <!-- Section tabs -->
    <div class="flex gap-1 mb-6 p-1 rounded-xl border border-border/60 bg-white" >
      <button
        v-for="s in SECTIONS"
        :key="s.id"
        class="flex-1 py-2 rounded-lg text-xs font-medium transition-colors"
        :class="activeSection === s.id ? 'bg-white/8 text-ink' : 'text-muted hover:text-ink'"
        @click="activeSection = s.id"
      >
        {{ s.label }}
      </button>
    </div>

    <form @submit.prevent="handleSubmit">
      <!-- IDENTIFICACIÓN -->
      <div v-show="activeSection === 'identificacion'" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5" >
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Nombre del cliente *</label>
            <input v-model="form.nombre_cliente" type="text" required class="input-field" placeholder="Ej: Brand Company S.L." />
            <p v-if="errors.nombre_cliente" class="text-xs text-red-400 mt-1">{{ errors.nombre_cliente }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Tipo de cliente</label>
            <select v-model="form.tipo_cliente" class="select-field">
              <option value="">Seleccionar tipo…</option>
              <option v-for="t in store.types" :key="t.id" :value="t.id">{{ t.nombre }}</option>
            </select>
            <p v-if="errors.tipo_cliente" class="text-xs text-red-400 mt-1">{{ errors.tipo_cliente }}</p>
          </div>
          <div>
            <p class="block text-xs font-medium text-muted mb-1.5">ID del cliente</p>
            <p class="text-xs text-muted/60 italic mt-2">Se asignará automáticamente</p>
          </div>
        </div>
        <div class="flex justify-end pt-2">
          <button type="button" class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors" @click="activeSection = 'facturacion'">
            Siguiente →
          </button>
        </div>
      </div>

      <!-- FACTURACIÓN -->
      <div v-show="activeSection === 'facturacion'" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-4" >
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Nombre de facturación *</label>
            <input v-model="form.nombre_facturacion" type="text" required class="input-field" placeholder="Razón social" />
            <p v-if="errors.nombre_facturacion" class="text-xs text-red-400 mt-1">{{ errors.nombre_facturacion }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">CIF *</label>
            <input v-model="form.cif" type="text" required class="input-field" placeholder="B12345678" />
            <p v-if="errors.cif" class="text-xs text-red-400 mt-1">{{ errors.cif }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Email de facturación *</label>
            <input v-model="form.email_facturacion" type="email" required class="input-field" placeholder="facturas@empresa.com" />
            <p v-if="errors.email_facturacion" class="text-xs text-red-400 mt-1">{{ errors.email_facturacion }}</p>
          </div>
          <div class="col-span-2">
            <label class="block text-xs font-medium text-muted mb-1.5">Dirección de facturación *</label>
            <input v-model="form.direccion_facturacion" type="text" required class="input-field" placeholder="Calle, número, piso…" />
            <p v-if="errors.direccion_facturacion" class="text-xs text-red-400 mt-1">{{ errors.direccion_facturacion }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Código postal *</label>
            <input v-model="form.codigo_postal" type="text" required class="input-field" placeholder="28001" />
            <p v-if="errors.codigo_postal" class="text-xs text-red-400 mt-1">{{ errors.codigo_postal }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">Ciudad *</label>
            <input v-model="form.ciudad" type="text" required class="input-field" placeholder="Madrid" />
            <p v-if="errors.ciudad" class="text-xs text-red-400 mt-1">{{ errors.ciudad }}</p>
          </div>
          <div>
            <label class="block text-xs font-medium text-muted mb-1.5">País</label>
            <input v-model="form.pais" type="text" class="input-field" />
          </div>
        </div>
        <div class="flex justify-between pt-2">
          <button type="button" class="h-9 px-5 rounded-xl border border-border/60 bg-white text-xs text-muted hover:text-ink transition-colors" @click="activeSection = 'identificacion'">
            ← Anterior
          </button>
          <button type="button" class="h-9 px-5 rounded-xl bg-white/6 text-ink text-xs font-medium hover:bg-white/10 transition-colors" @click="activeSection = 'contrato'">
            Siguiente →
          </button>
        </div>
      </div>

      <!-- CONTRATO -->
      <div v-show="activeSection === 'contrato'" class="rounded-2xl border border-border/60 bg-white shadow-card p-6 space-y-5" >
        <!-- Contrato firmado -->
        <label class="flex items-center gap-3 cursor-pointer group">
          <div
            class="w-5 h-5 rounded-md border flex-shrink-0 flex items-center justify-center transition-colors"
            :class="form.contrato_firmado ? 'bg-gold border-gold' : 'border-border group-hover:border-subtle'"
            @click="form.contrato_firmado = !form.contrato_firmado"
          >
            <svg v-if="form.contrato_firmado" class="w-3 h-3 text-ink" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <span class="text-sm text-ink">Contrato firmado</span>
        </label>

        <!-- File upload -->
        <div>
          <label class="block text-xs font-medium text-muted mb-2">Archivo de contrato <span class="text-subtle">(PDF, DOC…)</span></label>
          <label
            class="flex flex-col items-center justify-center gap-2 h-28 rounded-xl border border-dashed border-border hover:border-gold/40 hover:bg-gold/4 cursor-pointer transition-colors"
          >
            <svg class="w-6 h-6 text-muted" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <span class="text-xs text-muted">
              {{ contratoFile ? contratoFile.name : 'Haz clic o arrastra un archivo aquí' }}
            </span>
            <input type="file" class="hidden" accept=".pdf,.doc,.docx,.png,.jpg" @change="handleFile" />
          </label>
        </div>

        <!-- Errors generales -->
        <div v-if="errors.general || errors.non_field_errors" class="rounded-xl border border-red-500/20 bg-red-500/8 p-3 text-xs text-red-400">
          {{ errors.general || errors.non_field_errors }}
        </div>

        <div class="flex justify-between pt-2">
          <button type="button" class="h-9 px-5 rounded-xl border border-border/60 bg-white text-xs text-muted hover:text-ink transition-colors" @click="activeSection = 'facturacion'">
            ← Anterior
          </button>
          <button
            type="submit"
            :disabled="isLoading"
            class="h-9 px-6 rounded-xl bg-gold text-ink text-xs font-semibold flex items-center gap-2 hover:bg-gold/90 active:scale-[0.98] disabled:opacity-60 transition-all"
          >
            <svg v-if="isLoading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ isLoading ? 'Guardando…' : 'Dar de alta cliente' }}
          </button>
        </div>
      </div>
    </form>
  </div>
</template>
