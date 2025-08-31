# 必要なライブラリをインポート
import os
from dotenv import load_dotenv
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# .envファイルから環境変数を読み込む
load_dotenv()

# Tavily MCPクライアントを作成
tavily_mcp = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")}
    )
))

# チャットエージェント（既存知識で回答）
@tool
def chat_agent(query: str):
    """一般的な質問に既存の知識で回答します"""
    from strands.models.bedrock import BedrockModel
    
    print(f"🐥 chat_agent呼び出されました")

    model = BedrockModel(
        # model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        max_tokens=300
    )
    
    agent = Agent(
        model=model,
        system_prompt="簡潔で分かりやすく回答してください。"
    )

    print(f"🐥 chat_agentクエリ実行前...")

    return str(agent(query))

# Web検索エージェント（Tavily MCPを使用）
@tool
def web_search_agent(query: str):
    """Web検索を使って最新情報を調べて回答します"""
    from strands.models.bedrock import BedrockModel
    
    with tavily_mcp:
        model = BedrockModel(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            # max_tokens=400
        )
        
        agent = Agent(
            model=model,
            system_prompt="Web検索で最新情報を調べ、簡潔に回答してください。重要なポイントのみ含めてください。",
            tools=tavily_mcp.list_tools_sync()
        )
        return str(agent(query))

# Knowledge Baseエージェント
@tool
def knowledge_base_agent(query: str):
    """Knowledge Baseから関連情報を検索して回答します"""
    import boto3
    from strands.models.bedrock import BedrockModel
    
    # Bedrock Agent Runtimeクライアント（Knowledge Base用）
    kb_region = os.getenv('KNOWLEDGE_BASE_REGION', 'ap-northeast-1')
    model_region = os.getenv('AWS_REGION', 'us-east-1')
    print(f"🌍 Knowledge Baseリージョン: {kb_region}")
    print(f"🌍 モデルリージョン: {model_region}")
    
    bedrock_agent = boto3.client(
        'bedrock-agent-runtime',
        region_name=kb_region
    )
    
    print('📚 Knowledge Baseエージェントが呼び出されました')

    try:
        print(f"🔍 Knowledge Base ID: {os.getenv('KNOWLEDGE_BASE_ID')}")
        print(f"🔍 検索クエリ: {query}")
        
        MODEL_ARN_RERANK = "arn:aws:bedrock:ap-northeast-1::foundation-model/amazon.rerank-v1:0"

        # Knowledge Baseから検索（ハイブリッド + リランキング）
        try:
            # リランキング付きで試行
            kb_response = bedrock_agent.retrieve(
                knowledgeBaseId=os.getenv('KNOWLEDGE_BASE_ID'),
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10,
                        'overrideSearchType': 'HYBRID',
                        'rerankingConfiguration': {
                            'bedrockRerankingConfiguration': {
                                'modelConfiguration': {
                                    'modelArn': f'arn:aws:bedrock:{kb_region}::foundation-model/amazon.rerank-v1:0'
                                },
                                'numberOfRerankedResults': 3,
                            },
                            "type": "BEDROCK_RERANKING_MODEL"
                        }
                    }
                }
            )
            print(f"🔄 ハイブリッド検索 + Amazon Rerank v1.0 使用")
            
        except Exception as rerank_error:
            print(f"⚠️  リランキングエラー: {rerank_error}")
            print("🔄 ハイブリッド検索のみで再試行")
            
            # リランキングなしでフォールバック
            kb_response = bedrock_agent.retrieve(
                knowledgeBaseId=os.getenv('KNOWLEDGE_BASE_ID'),
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5,
                        'overrideSearchType': 'HYBRID'
                    }
                }
            )
            print(f"🔄 ハイブリッド検索使用（ベクター + キーワード）")
        
        print(f"✅ Knowledge Base検索成功")
        print(f"📊 検索結果数: {len(kb_response.get('retrievalResults', []))}")
        
        # 検索結果を整理
        context = ""
        for i, result in enumerate(kb_response.get('retrievalResults', [])):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            print(f"📄 結果{i+1} (スコア: {score:.3f}): {content[:100]}...")
            context += f"- {content}\n"
        
        if not context:
            print("⚠️  Knowledge Baseに関連情報が見つかりません")
            return "Knowledge Baseに関連する情報が見つかりませんでした。"
        
        # print("🤖 KnoeledgeBase検索結果取得完了")
        # return f"Knowledge Base検索結果:\n{context}"
    
        # 検索結果を基に回答生成
        print("🤖 回答生成中...")
        model = BedrockModel(
            # model="us.anthropic.claude-3-5-haiku-20241022-v1:0"
            # model="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",

            temperature=0.0,
            max_tokens=1024,
            top_p=0.1,
            top_k=1,
            # Trueにするとストリーミングで出力される。
            # ストリーミングでツール利用がサポートされないモデルがあるため、OFF
            streaming=False 

        )
        
        agent = Agent(
            model=model,
            system_prompt=f"以下のKnowledge Baseの情報を基に、質問に簡潔に回答してください。\n\n{context}"
        )
        
        return str(agent(query))
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Knowledge Baseエラー詳細:")
        print(f"   エラータイプ: {type(e).__name__}")
        print(f"   エラーメッセージ: {str(e)}")
        print(f"   スタックトレース:\n{error_details}")
        return f"Knowledge Base検索エラー: {str(e)}"

# オーケストレーター（判断して適切なエージェントを使用）
from strands.models.bedrock import BedrockModel

orchestrator_model = BedrockModel(
    model="us.anthropic.claude-3-5-haiku-20241022-v1:0"
    # model="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    # model="us.anthropic.claude-sonnet-4-20250514-v1:0"
    # max_tokens=1000
)

orchestrator = Agent(
    model=orchestrator_model,
    system_prompt="""質問を分析して適切なエージェントに振り分けてください。
    
    - 通常の回答 → chat_agent
    - ナレッジベースを使った回答（ジョジョの奇妙な冒険、AWS系の質問） → knowledge_base_agent
    
    エージェントの回答をそのまま返してください。""",
    tools=[chat_agent, knowledge_base_agent]
)

# レスポンス取得関数
def get_response(question: str):
    """質問に対する回答を取得"""
    return str(orchestrator(question))

# インタラクティブチャット
if __name__ == "__main__":
    print("=== AI チャットボット ===")
    print("質問を入力してください（'quit'で終了）")
    print("="*40)
    
    while True:
        try:
            question = input("\n質問: ")
            
            if question.lower() in ['quit', 'exit', '終了']:
                print("チャットを終了します。")
                break
                
            if not question.strip():
                continue
                
            print("\n回答中...")
            result = get_response(question)
            print(f"\n回答: {result}")
            
        except KeyboardInterrupt:
            print("\n\nチャットを終了します。")
            break
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            print("もう一度お試しください。")