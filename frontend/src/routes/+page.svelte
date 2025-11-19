<script lang="ts">
	import { onMount } from 'svelte';
	import { diagramStore, currentDiagram, createNewDiagram } from '$lib/stores/diagram';
	import { api } from '$lib/services/api';
	import { websocketService } from '$lib/services/websocket';
	import DiagramEditor from '$lib/components/DiagramEditor.svelte';
	import DiagramPreview from '$lib/components/DiagramPreview.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import AiAssistant from '$lib/components/AiAssistant.svelte';
	import { toast } from 'svelte-sonner';

	let editorView: 'split' | 'code' | 'preview' = 'split';
	let isFullscreen = false;

	// Create initial diagram if none exists
	onMount(() => {
		const unsubscribe = currentDiagram.subscribe(diagram => {
			if (!diagram) {
				const newDiagram = createNewDiagram(
					`graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Do this]
    B -->|No| D[Do that]
    C --> E[End]
    D --> E`,
					'Welcome Diagram'
				);
				diagramStore.addDiagram(newDiagram);
			}
		});

		return unsubscribe;
	});

	// Handle keyboard shortcuts
	function handleKeydown(e: KeyboardEvent) {
		// Cmd/Ctrl + S to save
		if ((e.metaKey || e.ctrlKey) && e.key === 's') {
			e.preventDefault();
			handleSave();
		}
		// Cmd/Ctrl + Enter to render
		if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
			e.preventDefault();
			handleRender();
		}
		// Cmd/Ctrl + / to toggle AI assistant
		if ((e.metaKey || e.ctrlKey) && e.key === '/') {
			e.preventDefault();
			// Toggle AI assistant visibility (handled in AiAssistant component)
		}
		// F11 to toggle fullscreen
		if (e.key === 'F11') {
			e.preventDefault();
			toggleFullscreen();
		}
	}

	async function handleSave() {
		const diagram = $currentDiagram;
		if (!diagram) return;

		diagramStore.setSaving(true);
		try {
			// Validate diagram first
			const validation = await api.validateDiagram({ code: diagram.code });
			
			if (validation.success && validation.data) {
				diagramStore.updateDiagram(diagram.id, {
					validation: {
						is_valid: validation.data.is_valid,
						errors: validation.data.errors?.map(e => e.message),
						warnings: validation.data.warnings?.map(w => w.message)
					},
					type: validation.data.diagram_type
				});

				if (validation.data.is_valid) {
					toast.success('Diagram saved successfully');
				} else {
					toast.warning('Diagram saved with validation errors');
				}
			}
		} catch (error) {
			toast.error('Failed to save diagram');
			console.error('Save error:', error);
		} finally {
			diagramStore.setSaving(false);
		}
	}

	async function handleRender() {
		const diagram = $currentDiagram;
		if (!diagram || !diagram.validation?.is_valid) {
			toast.error('Please fix validation errors before rendering');
			return;
		}

		try {
			const response = await api.renderDiagram({
				code: diagram.code,
				format: 'png',
				theme: $diagramStore.theme,
				style: $diagramStore.style
			});

			if (response.success && response.data?.data) {
				// Handle rendered image (update preview)
				toast.success('Diagram rendered successfully');
			} else {
				toast.error(response.error?.message || 'Failed to render diagram');
			}
		} catch (error) {
			toast.error('Failed to render diagram');
			console.error('Render error:', error);
		}
	}

	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
		if (isFullscreen) {
			document.documentElement.requestFullscreen();
		} else {
			document.exitFullscreen();
		}
	}

	// Listen for WebSocket validation responses
	$: if (websocketService.isConnected) {
		websocketService.on('validation', (message) => {
			if ('valid' in message && $currentDiagram) {
				diagramStore.updateDiagram($currentDiagram.id, {
					validation: {
						is_valid: message.valid,
						errors: message.error ? [message.error] : []
					}
				});
			}
		});
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="editor-container" class:fullscreen={isFullscreen}>
	<Sidebar />
	
	<div class="editor-main">
		<!-- Toolbar -->
		<div class="toolbar">
			<div class="toolbar-section">
				<button 
					class="tool-button" 
					class:active={editorView === 'code'}
					on:click={() => editorView = 'code'}
					title="Code only (Ctrl+1)"
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polyline points="16 18 22 12 16 6"></polyline>
						<polyline points="8 6 2 12 8 18"></polyline>
					</svg>
				</button>
				<button 
					class="tool-button" 
					class:active={editorView === 'split'}
					on:click={() => editorView = 'split'}
					title="Split view (Ctrl+2)"
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
						<line x1="12" y1="3" x2="12" y2="21"></line>
					</svg>
				</button>
				<button 
					class="tool-button" 
					class:active={editorView === 'preview'}
					on:click={() => editorView = 'preview'}
					title="Preview only (Ctrl+3)"
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
						<circle cx="12" cy="12" r="3"></circle>
					</svg>
				</button>
			</div>

			<div class="toolbar-section">
				<button 
					class="tool-button primary" 
					on:click={handleSave}
					disabled={$diagramStore.isSaving}
					title="Save diagram (Ctrl+S)"
				>
					{#if $diagramStore.isSaving}
						<span class="spinner"></span>
					{:else}
						Save
					{/if}
				</button>
				<button 
					class="tool-button" 
					on:click={handleRender}
					title="Render diagram (Ctrl+Enter)"
				>
					Render
				</button>
				<button 
					class="tool-button" 
					on:click={toggleFullscreen}
					title="Toggle fullscreen (F11)"
				>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						{#if isFullscreen}
							<path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
						{:else}
							<path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
						{/if}
					</svg>
				</button>
			</div>
		</div>

		<!-- Editor Content -->
		<div class="editor-content" data-view={editorView}>
			{#if editorView === 'code' || editorView === 'split'}
				<div class="editor-pane">
					<DiagramEditor />
				</div>
			{/if}
			
			{#if editorView === 'preview' || editorView === 'split'}
				<div class="preview-pane">
					<DiagramPreview />
				</div>
			{/if}
		</div>
	</div>

	<AiAssistant />
</div>

<style>
	.editor-container {
		display: flex;
		height: 100vh;
		overflow: hidden;
		background: var(--background);
	}

	.editor-container.fullscreen {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 9999;
	}

	.editor-main {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: var(--card);
		border-bottom: 1px solid var(--border);
		gap: 1rem;
	}

	.toolbar-section {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.tool-button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.5rem 1rem;
		background: transparent;
		color: var(--foreground);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		min-width: 2.5rem;
		height: 2.5rem;
	}

	.tool-button:hover {
		background: var(--secondary);
		border-color: var(--secondary-foreground);
	}

	.tool-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.tool-button.active {
		background: var(--primary);
		color: var(--primary-foreground);
		border-color: var(--primary);
	}

	.tool-button.primary {
		background: var(--primary);
		color: var(--primary-foreground);
		border-color: var(--primary);
	}

	.tool-button.primary:hover {
		opacity: 0.9;
	}

	.editor-content {
		flex: 1;
		display: flex;
		overflow: hidden;
	}

	.editor-content[data-view="code"] .editor-pane {
		flex: 1;
	}

	.editor-content[data-view="preview"] .preview-pane {
		flex: 1;
	}

	.editor-content[data-view="split"] .editor-pane,
	.editor-content[data-view="split"] .preview-pane {
		flex: 1;
	}

	.editor-pane,
	.preview-pane {
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.editor-content[data-view="split"] .editor-pane {
		border-right: 1px solid var(--border);
	}

	.spinner {
		display: inline-block;
		width: 14px;
		height: 14px;
		border: 2px solid transparent;
		border-top-color: currentColor;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@media (max-width: 768px) {
		.editor-content[data-view="split"] {
			flex-direction: column;
		}

		.editor-content[data-view="split"] .editor-pane {
			border-right: none;
			border-bottom: 1px solid var(--border);
		}
	}
</style>