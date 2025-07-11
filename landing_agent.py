import os
import json
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import datetime
import re
import base64

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Verifica se a API key está configurada
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("⚠️  AVISO: ANTHROPIC_API_KEY não encontrada no .env")
    client = None
else:
    client = Anthropic(api_key=api_key)

# Interface do agente
AGENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🎨 Landing Page Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, system-ui, sans-serif;
            background: #000;
            color: #fff;
            overflow-x: hidden;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 60px 20px;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(79, 70, 229, 0.3) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        h1 {
            font-size: 3.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }
        
        .subtitle {
            font-size: 1.2rem;
            color: #94a3b8;
            position: relative;
            z-index: 1;
        }
        
        .chat-container {
            background: #0f0f0f;
            border: 1px solid #1e293b;
            border-radius: 20px;
            padding: 30px;
            margin: 40px auto;
            max-width: 800px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        }
        
        #chat {
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 20px;
            background: #050505;
            border-radius: 12px;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px 20px;
            border-radius: 12px;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin-left: 20%;
            color: white;
        }
        
        .assistant {
            background: #1e293b;
            margin-right: 20%;
        }
        
        .system {
            background: #065f46;
            text-align: center;
            font-style: italic;
        }
        
        .input-area {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        #user-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #1e293b;
            border-radius: 12px;
            background: #0a0a0a;
            color: white;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        #user-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .preview-container {
            display: none;
            margin-top: 40px;
            padding: 30px;
            background: #0f0f0f;
            border: 1px solid #1e293b;
            border-radius: 20px;
        }
        
        .preview-container.show { display: block; }
        
        .preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .preview-actions {
            display: flex;
            gap: 10px;
        }
        
        .preview-frame {
            width: 100%;
            height: 600px;
            border: 1px solid #1e293b;
            border-radius: 12px;
            background: white;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #1e293b;
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .examples {
            margin: 40px auto;
            max-width: 800px;
            padding: 20px;
            background: #0f0f0f;
            border-radius: 20px;
            border: 1px solid #1e293b;
        }
        
        .examples h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .example-item {
            padding: 10px 15px;
            margin: 5px 0;
            background: #1a1a1a;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .example-item:hover {
            background: #1e293b;
            transform: translateX(5px);
        }
        
        code {
            background: #1e293b;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Landing Page Generator</h1>
            <p class="subtitle">Crie landing pages incríveis com IA em segundos</p>
        </div>
        
        <div class="chat-container">
            <div id="chat"></div>
            <div class="input-area">
                <input type="text" id="user-input" placeholder="Descreva a landing page que deseja criar..." autocomplete="off">
                <button onclick="sendMessage()">Gerar</button>
            </div>
        </div>
        
        <div id="preview-container" class="preview-container">
            <div class="preview-header">
                <h2>Preview da Landing Page</h2>
                <div class="preview-actions">
                    <button onclick="downloadHTML()" style="background: #059669;">💾 Download HTML</button>
                    <button onclick="openInNewTab()" style="background: #7c3aed;">🚀 Abrir em Nova Aba</button>
                    <button onclick="copyHTML()" style="background: #ea580c;">📋 Copiar Código</button>
                </div>
            </div>
            <iframe id="preview-frame" class="preview-frame"></iframe>
        </div>
        
        <div class="examples">
            <h3>💡 Exemplos de prompts:</h3>
            <div class="example-item" onclick="useExample(this)">
                Landing page para startup de IA com hero animado, depoimentos e CTA
            </div>
            <div class="example-item" onclick="useExample(this)">
                Página de produto SaaS com pricing cards, features em grid e animações suaves
            </div>
            <div class="example-item" onclick="useExample(this)">
                Landing page minimalista para app mobile com mockups 3D e gradientes
            </div>
            <div class="example-item" onclick="useExample(this)">
                Página de evento tech com countdown, speakers e formulário de inscrição
            </div>
            <div class="example-item" onclick="useExample(this)">
                Portfolio criativo com parallax, galeria interativa e animações on scroll
            </div>
        </div>
    </div>

    <script>
        let currentHTML = '';
        let currentFilename = '';
        
        function addMessage(content, type) {
            const chat = document.getElementById('chat');
            const msg = document.createElement('div');
            msg.className = 'message ' + type;
            msg.innerHTML = content;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            input.disabled = true;
            
            addMessage('<div class="loading"></div> Gerando landing page...', 'assistant');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: message})
                });
                
                const data = await response.json();
                const messages = document.querySelectorAll('.message');
                messages[messages.length - 1].remove();
                
                if (data.success) {
                    addMessage(data.message, 'assistant');
                    currentHTML = data.html;
                    currentFilename = data.filename;
                    
                    // Mostra preview
                    const iframe = document.getElementById('preview-frame');
                    iframe.srcdoc = currentHTML;
                    document.getElementById('preview-container').classList.add('show');
                    
                    addMessage('✨ Landing page gerada com sucesso! Veja o preview abaixo.', 'system');
                } else {
                    addMessage('❌ ' + data.message, 'system');
                }
            } catch (error) {
                addMessage('❌ Erro: ' + error.message, 'system');
            }
            
            input.disabled = false;
            input.focus();
        }
        
        function downloadHTML() {
            if (!currentHTML) return;
            
            const blob = new Blob([currentHTML], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFilename;
            a.click();
            URL.revokeObjectURL(url);
            
            addMessage('📥 Download iniciado: ' + currentFilename, 'system');
        }
        
        function openInNewTab() {
            if (!currentHTML) return;
            
            const blob = new Blob([currentHTML], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
            
            setTimeout(() => URL.revokeObjectURL(url), 100);
        }
        
        function copyHTML() {
            if (!currentHTML) return;
            
            navigator.clipboard.writeText(currentHTML).then(() => {
                addMessage('📋 Código HTML copiado!', 'system');
            }).catch(err => {
                addMessage('❌ Erro ao copiar: ' + err.message, 'system');
            });
        }
        
        function useExample(element) {
            const input = document.getElementById('user-input');
            input.value = element.textContent.trim();
            input.focus();
        }
        
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        addMessage('Olá! Eu crio landing pages incríveis sob demanda. Descreva o que você precisa e vou gerar um HTML completo com design moderno, animações e interatividade!', 'assistant');
    </script>
</body>
</html>
"""

# Prompt especializado para landing pages
LANDING_PROMPT = """Você é um expert em criar landing pages modernas e impressionantes.

PRINCÍPIOS DE DESIGN:
1. Design que impressiona - cores vibrantes, gradientes, animações suaves
2. Mobile-first e totalmente responsivo
3. Performance otimizada - código limpo e eficiente
4. Acessibilidade mantida mesmo com visual rico
5. Interatividade com HTMX quando apropriado

STACK OBRIGATÓRIA:
- HTML5 semântico
- Tailwind CSS via CDN
- HTMX para interatividade (quando necessário)
- Alpine.js para estado local (quando necessário)
- Font Awesome para ícones
- Google Fonts para tipografia
- AOS (Animate On Scroll) para animações
- Particles.js ou similar para efeitos visuais (quando apropriado)

ESTRUTURA DA LANDING PAGE:
1. Hero Section impactante com CTA claro
2. Features/Benefits em layout criativo
3. Social Proof (depoimentos, logos, números)
4. Pricing ou Products (se aplicável)
5. FAQ ou How it Works
6. Footer com links e informações

ELEMENTOS OBRIGATÓRIOS:
- Animações CSS customizadas
- Efeitos hover criativos
- Gradientes modernos
- Sombras e depth
- Microinterações
- Loading animations
- Scroll animations
- Parallax effects (quando apropriado)

IMPORTANTE:
- Gere HTML COMPLETO em um único arquivo
- Inclua todos os estilos inline ou em <style>
- Use CDNs para todas as bibliotecas
- Otimize para conversão
- Inclua meta tags para SEO
- Teste de legibilidade com contrastes adequados

Responda SEMPRE com o HTML completo após a tag [LANDING_HTML].
Antes do HTML, faça um breve resumo do que foi criado.
"""

# Armazena contexto
conversation_context = []

@app.route('/')
def home():
    return render_template_string(AGENT_HTML)

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json.get('prompt', '')
    
    if not client:
        return jsonify({
            'success': False,
            'message': 'API Key da Anthropic não configurada!'
        }), 400
    
    try:
        # Chama Claude para gerar a landing page
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            temperature=0.8,  # Mais criatividade para designs
            system=LANDING_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Extrai o HTML
        if "[LANDING_HTML]" in response_text:
            html_match = re.search(r'\[LANDING_HTML\](.*?)$', response_text, re.DOTALL)
            if html_match:
                html_content = html_match.group(1).strip()
                
                # Gera nome do arquivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"landing_page_{timestamp}.html"
                
                # Salva o arquivo
                output_dir = Path("generated_pages")
                output_dir.mkdir(exist_ok=True)
                
                with open(output_dir / filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Extrai resumo
                summary = response_text.split("[LANDING_HTML]")[0].strip()
                
                return jsonify({
                    'success': True,
                    'message': summary,
                    'html': html_content,
                    'filename': filename
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Não foi possível extrair o HTML da resposta'
                })
        else:
            return jsonify({
                'success': False,
                'message': 'Resposta incompleta do modelo'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar: {str(e)}'
        }), 500

@app.route('/pages')
def list_pages():
    """Lista páginas geradas anteriormente"""
    output_dir = Path("generated_pages")
    if not output_dir.exists():
        return jsonify([])
    
    pages = []
    for file in output_dir.glob("*.html"):
        pages.append({
            'filename': file.name,
            'created': datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            'size': file.stat().st_size
        })
    
    return jsonify(sorted(pages, key=lambda x: x['created'], reverse=True))

@app.route('/pages/<filename>')
def get_page(filename):
    """Retorna uma página específica"""
    output_dir = Path("generated_pages")
    file_path = output_dir / filename
    
    if file_path.exists() and file_path.suffix == '.html':
        return send_file(file_path, mimetype='text/html')
    else:
        return "Página não encontrada", 404

if __name__ == '__main__':
    print("🎨 Landing Page Generator")
    print("📍 Acesse: http://localhost:5001")  # Porta diferente para não conflitar
    print("✨ Crie landing pages incríveis com IA!")
    app.run(debug=True, port=5001)