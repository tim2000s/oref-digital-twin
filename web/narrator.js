/*
 * The in-browser narrator, in a module Web Worker: WebLLM running a small instruct model on
 * the device's GPU through WebGPU. The page talks to it with WebWorkerMLCEngine (app.js).
 *
 * It runs in a worker rather than on the page because the page's CSP forbids compiling
 * WebAssembly, and so the page stays responsive while the model loads. web-llm.js is fetched
 * and checked against a pinned digest by build.sh.
 */
import { WebWorkerMLCEngineHandler } from './web-llm.js';

const handler = new WebWorkerMLCEngineHandler();
self.onmessage = (msg) => handler.onmessage(msg);
