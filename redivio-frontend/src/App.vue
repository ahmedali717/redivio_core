<template>
  <div class="flex h-screen bg-gray-50 font-sans">
    
    <aside class="w-64 bg-[#0f172a] text-white flex flex-col shadow-2xl z-20">
      <div class="h-16 flex items-center px-6 border-b border-gray-700 bg-[#1e293b]">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3 font-bold">R</div>
        <span class="text-lg font-bold tracking-wide">Redivio ERP</span>
      </div>

      <nav class="flex-1 py-6 px-3 space-y-2">
        <div class="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">Apps</div>
        
        <a href="#" class="flex items-center px-3 py-2.5 bg-blue-600 rounded-lg text-white shadow-lg shadow-blue-900/50 transition-all">
          <span class="mr-3 text-lg">🏢</span>
          <span class="font-medium">Org Builder</span>
        </a>

        <a href="#" class="flex items-center px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all group">
          <span class="mr-3 text-lg group-hover:scale-110 transition">📦</span>
          <span class="font-medium">WMS (المخازن)</span>
        </a>

        <a href="#" class="flex items-center px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all group">
          <span class="mr-3 text-lg group-hover:scale-110 transition">🛒</span>
          <span class="font-medium">Procurement</span>
        </a>
        
        <a href="#" class="flex items-center px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all group">
          <span class="mr-3 text-lg group-hover:scale-110 transition">💰</span>
          <span class="font-medium">Sales</span>
        </a>
      </nav>

      <div class="p-4 border-t border-gray-700 bg-[#1e293b]">
        <div class="flex items-center">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 mr-3"></div>
          <div>
            <p class="text-sm font-medium">Admin User</p>
            <p class="text-xs text-gray-400">Super Admin</p>
          </div>
        </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col relative overflow-hidden">
      
      <header class="h-16 bg-white border-b border-gray-200 flex justify-between items-center px-8 shadow-sm z-10">
        <div class="flex items-center text-gray-500 text-sm">
          <span>App</span>
          <span class="mx-2">/</span>
          <span class="text-gray-800 font-semibold">Organization Structure</span>
        </div>
        <button class="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 text-sm font-medium transition shadow-sm">
          Save Changes
        </button>
      </header>

      <div class="flex-1 relative bg-gray-50" @drop="onDrop" @dragover="onDragOver">
        <VueFlow v-model="elements" :default-zoom="1.5" :min-zoom="0.2" :max-zoom="4" fit-view-on-init class="h-full w-full">
          <Background pattern-color="#cbd5e1" :gap="20" />
          <Controls />
        </VueFlow>

        <div class="absolute top-6 right-6 bg-white p-4 rounded-xl shadow-xl border border-gray-100 w-64 z-20">
          <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Construction Kit</h3>
          <div class="space-y-3">
            <div draggable="true" @dragstart="onDragStart($event, 'company')" class="flex items-center p-3 border border-gray-200 rounded-lg cursor-move hover:border-blue-500 hover:shadow-md transition bg-white select-none">
              <span class="text-xl mr-3">🏢</span>
              <span class="text-sm font-medium text-gray-700">Company</span>
            </div>
            <div draggable="true" @dragstart="onDragStart($event, 'plant')" class="flex items-center p-3 border border-gray-200 rounded-lg cursor-move hover:border-blue-500 hover:shadow-md transition bg-white select-none">
              <span class="text-xl mr-3">🏭</span>
              <span class="text-sm font-medium text-gray-700">Warehouse (Plant)</span>
            </div>
            <div draggable="true" @dragstart="onDragStart($event, 'bin')" class="flex items-center p-3 border border-gray-200 rounded-lg cursor-move hover:border-blue-500 hover:shadow-md transition bg-white select-none">
              <span class="text-xl mr-3">🗄️</span>
              <span class="text-sm font-medium text-gray-700">Storage Bin</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

// 1. الحالة المبدئية (Initial Elements)
const elements = ref([
  { 
    id: '1', 
    type: 'input', 
    label: 'Redivio HQ', 
    position: { x: 250, y: 5 },
    style: { background: '#1e293b', color: 'white', border: 'none', padding: '15px', borderRadius: '8px', fontWeight: 'bold', width: '200px' }
  },
  { 
    id: '2', 
    label: 'Main Warehouse', 
    position: { x: 100, y: 150 },
    style: { background: '#ffffff', border: '2px solid #3b82f6', borderRadius: '8px', padding: '10px', width: '180px' }
  },
  { 
    id: '3', 
    label: 'Distribution Center', 
    position: { x: 400, y: 150 },
    style: { background: '#ffffff', border: '2px solid #3b82f6', borderRadius: '8px', padding: '10px', width: '180px' }
  },
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e1-3', source: '1', target: '3', animated: true },
])

const { addNodes, project, vueFlowRef } = useVueFlow()

// 2. دوال السحب والإفلات (Drag & Drop Logic)
const onDragStart = (event, nodeType) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }
}

const onDragOver = (event) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const onDrop = (event) => {
  const type = event.dataTransfer?.getData('application/vueflow')
  
  // حساب المكان اللي الماوس ساب فيه العنصر
  const { left, top } = document.querySelector('.vue-flow__renderer').getBoundingClientRect()
  const position = project({ 
    x: event.clientX - left - 100, 
    y: event.clientY - top 
  })

  const newNode = {
    id: Math.random().toString(),
    type: 'default', // ممكن نغيره حسب النوع
    label: type === 'plant' ? 'New Warehouse' : type === 'bin' ? 'Bin A-01' : 'New Company',
    position,
    style: { 
      background: '#fff', 
      border: '1px solid #777', 
      padding: '10px', 
      borderRadius: '5px',
      width: '150px'
    },
  }

  addNodes([newNode])
}
</script>

<style>
/* تحسينات إضافية للخطوط */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
body { font-family: 'Inter', sans-serif; }
</style>