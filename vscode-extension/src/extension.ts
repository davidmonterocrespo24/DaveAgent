import * as vscode from 'vscode';
import { SidebarProvider } from './sidebarProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('DaveAgent extension is active');

    const sidebarProvider = new SidebarProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            "daveagent.sidebar",
            sidebarProvider
        )
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('daveagent.start', () => {
            vscode.commands.executeCommand('workbench.view.extension.daveagent-view');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('daveagent.ask', async () => {
            const input = await vscode.window.showInputBox({ prompt: "Ask DaveAgent..." });
            if (input) {
                sidebarProvider._view?.webview.postMessage({
                    type: 'ask-from-command',
                    value: input
                });
            }
        })
    );
}

export function deactivate() { }
