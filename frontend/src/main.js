import '@arcgis/core/assets/esri/themes/dark/main.css'
import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

const app = mount(App, {
  target: document.getElementById('app'),
})

export default app