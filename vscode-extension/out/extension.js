"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const sidebarProvider_1 = require("./sidebarProvider");
function activate(context) {
    console.log('DaveAgent extension is active');
    const sidebarProvider = new sidebarProvider_1.SidebarProvider(context.extensionUri);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider("daveagent.sidebar", sidebarProvider));
    context.subscriptions.push(vscode.commands.registerCommand('daveagent.start', () => {
        vscode.commands.executeCommand('workbench.view.extension.daveagent-view');
    }));
    context.subscriptions.push(vscode.commands.registerCommand('daveagent.ask', async () => {
        const input = await vscode.window.showInputBox({ prompt: "Ask DaveAgent..." });
        if (input) {
            sidebarProvider._view?.webview.postMessage({
                type: 'ask-from-command',
                value: input
            });
        }
    }));
}
function deactivate() { }
//# sourceMappingURL=extension.js.map