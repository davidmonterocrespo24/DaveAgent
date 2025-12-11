import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

export class SidebarProvider implements vscode.WebviewViewProvider {
    _view?: vscode.WebviewView;
    _doc?: vscode.TextDocument;
    private _process?: cp.ChildProcess;
    private _extensionUri: vscode.Uri;

    constructor(extensionUri: vscode.Uri) {
        this._extensionUri = extensionUri;
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'userInput':
                    this._sendMessageToProcess(data.value);
                    break;
                case 'startAgent':
                    this._startDaveAgentProcess();
                    break;
                case 'killAgent':
                    this._killProcess();
                    break;
            }
        });
    }

    private _killProcess() {
        if (this._process) {
            this._process.kill();
            this._process = undefined;
            this._view?.webview.postMessage({ type: 'processExited' });
        }
    }

    private _startDaveAgentProcess() {
        const config = vscode.workspace.getConfiguration('daveagent');
        const pythonPath = config.get<string>('pythonPath') || 'python';
        const workspacePath = vscode.workspace.workspaceFolders?.[0].uri.fsPath || '';

        if (!workspacePath) {
            vscode.window.showErrorMessage('DaveAgent requires an open workspace.');
            return;
        }

        // We assume daveagent is installed in the python environment or available as a module
        // We'll try running 'python -m src.cli --vscode' from the workspace root or fallback location
        // IMPORTANT: In production, we might need a more robust way to find the CLI.
        // For now, we assume the user has the CodeAgent repo open or the package installed.
        // We will try to find src/cli.py relative to workspace or assume installed as module.

        // Command: python -m src.cli --vscode
        // Cwd: workspacePath

        console.log(`Starting DaveAgent with ${pythonPath} in ${workspacePath}`);

        this._process = cp.spawn(pythonPath, ['-m', 'src.cli', '--vscode'], {
            cwd: workspacePath,
            env: { ...process.env, PYTHONUNBUFFERED: '1' }
        });

        if (this._process.pid) {
            this._view?.webview.postMessage({ type: 'processStarted' });
        }

        this._process.stdout?.on('data', (data) => {
            const output = data.toString();
            console.log('DaveAgent OUT:', output);

            // Output might contain multiple JSON lines
            const lines = output.split('\n');
            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const message = JSON.parse(line);
                        this._handleAgentMessage(message);
                    } catch (e) {
                        console.error('Error parsing JSON from agent:', e, line);
                        // Forward non-JSON output as simple info
                        this._view?.webview.postMessage({
                            type: 'log',
                            value: `[Raw] ${line}`
                        });
                    }
                }
            }
        });

        this._process.stderr?.on('data', (data) => {
            console.error('DaveAgent ERR:', data.toString());
            this._view?.webview.postMessage({
                type: 'log',
                value: `[Error] ${data.toString()}`
            });
        });

        this._process.on('close', (code) => {
            console.log(`DaveAgent process exited with code ${code}`);
            this._process = undefined;
            this._view?.webview.postMessage({ type: 'processExited', code });
        });
    }

    private _sendMessageToProcess(text: string) {
        if (!this._process) {
            this._startDaveAgentProcess();
            // Wait a bit? Or just queue?
            // For now, let's just wait 1s ideally, but we'll try sending.
            // Actually if not started, we can't write to stdin yet.
            // We should auto-start on load or have explicit start button.
            // We added startAgent case.
            vscode.window.showErrorMessage("Agent not running. Press Start.");
            return;
        }

        // Construct JSON input msg
        const msg = JSON.stringify({ input: text }) + '\n';
        this._process.stdin?.write(msg);
    }

    private _handleAgentMessage(message: any) {
        // Forward generic messages to webview
        this._view?.webview.postMessage({
            type: 'agentEvent',
            data: message
        });

        // Handle specific VS Code actions if needed (e.g. open file)
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'style.css'));
        const iconUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'robot.svg'));

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleUri}" rel="stylesheet">
                <title>DaveAgent</title>
            </head>
            <body>
                <div class="header">
                    <img src="${iconUri}" class="logo" />
                    <h2>DaveAgent</h2>
                    <div class="controls">
                        <button id="start-btn">Start</button>
                        <button id="stop-btn" class="hidden">Stop</button>
                    </div>
                </div>
                
                <div id="chat-container">
                    <div class="message system">
                        Welcome to DaveAgent. Click Start to begin session.
                    </div>
                </div>

                <div class="input-area">
                    <textarea id="message-input" placeholder="Ask DaveAgent..." disabled></textarea>
                    <button id="send-btn" disabled>Send</button>
                </div>

                <script src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}
