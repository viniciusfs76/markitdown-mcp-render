#!/usr/bin/env python3
"""
Servidor MCP customizado que funciona corretamente
Substitui o servidor oficial que tem bugs
"""

import asyncio
import json
import subprocess
import base64
import tempfile
import os
from typing import Dict, Any, List
from aiohttp import web
import uuid

class CustomMCPServer:
    def __init__(self):
        self.tools = {
            "convert_to_markdown": {
                "name": "convert_to_markdown",
                "description": "Convert text or file content to Markdown using MarkItDown",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text content to convert to Markdown"
                        },
                        "file_content": {
                            "type": "string",
                            "description": "Base64 encoded file content"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "Name of the file being processed"
                        }
                    }
                }
            }
        }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "markitdown-custom-mcp",
                "version": "1.0.0"
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "tools": list(self.tools.values())
        }
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "convert_to_markdown":
            text = arguments.get("text", "")
            file_content = arguments.get("file_content", "")
            file_name = arguments.get("file_name", "")
            
            if file_content and file_name:
                # Process file content
                try:
                    file_data = base64.b64decode(file_content)
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(file_data)
                        tmp_file_path = tmp_file.name
                    
                    # Convert using markitdown
                    result = subprocess.run(
                        ['markitdown', tmp_file_path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    # Clean up
                    os.unlink(tmp_file_path)
                    
                    if result.returncode == 0:
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result.stdout
                                }
                            ]
                        }
                    else:
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error converting file: {result.stderr}"
                                }
                            ]
                        }
                except Exception as e:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error processing file: {str(e)}"
                            }
                        ]
                    }
            else:
                # Process text directly
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ]
            }
    
    async def handle_request(self, request):
        """Handle MCP request"""
        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")
            
            print(f"📥 Recebido: {method} (ID: {request_id})")
            
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            else:
                result = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            print(f"📤 Enviando: {json.dumps(result, indent=2)}")
            
            return web.json_response(response)
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "id": data.get("id") if 'data' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })
    
    async def create_app(self):
        """Create web application"""
        app = web.Application()
        app.router.add_post('/mcp', self.handle_request)
        
        # Add CORS middleware
        async def cors_middleware(request, handler):
            if request.method == 'OPTIONS':
                return web.Response(
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    }
                )
            
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        app.middlewares.append(cors_middleware)
        return app

async def main():
    """Main function"""
    server = CustomMCPServer()
    app = await server.create_app()
    
    print("🚀 Iniciando servidor MCP customizado...")
    print("   URL: http://0.0.0.0:3001/mcp")
    print("   Para n8n: http://localhost:3001/mcp")
    print("   Pressione Ctrl+C para parar")
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 3001)
    await site.start()
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\n👋 Parando servidor...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
