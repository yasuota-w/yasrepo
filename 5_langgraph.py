# 必要なライブラリをインポート
import os
from dotenv import load_dotenv
import boto3
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults

# .envファイルから環境変数を読み込む
load_dotenv()

# 状態の定義
class State(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    agent_type: str
    context: str

# チャットエージェント（既存知識で回答）
def chat_agent(state: State):
    """一般的な質問に既存の知識で回答します"""
    print("🐥 chat_agent呼び出されました")
    
    llm = ChatBedrock(
        # model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        model_kwargs={"max_tokens": 300}
    )
    
    response = llm.invoke([HumanMessage(content=f"簡潔で分かりやすく回答してください。\n\n質問: {state['query']}")])
    
    return {
        "messages": [AIMessage(content=response.content)],
        "context": response.content
    }

# Web検索エージェント（Tavily使用）
def web_search_agent(state: State):
    """Web検索を使って最新情報を調べて回答します"""
    print("🌐 web_search_agent呼び出されました")
    
    query = state['query']
    
    try:
        # Tavily検索ツールを初期化
        search = TavilySearchResults(
            max_results=5,
            api_key=os.getenv("TAVILY_API_KEY")
        )
        
        # Web検索実行
        print(f"🔍 Web検索実行: {query}")
        search_results = search.invoke({"query": query})
        
        # 検索結果を整理
        context = "Web検索結果:\n"
        for i, result in enumerate(search_results[:3]):  # 上位3件
            title = result.get('title', '')
            content = result.get('content', '')
            url = result.get('url', '')
            context += f"\n{i+1}. {title}\n{content[:200]}...\nURL: {url}\n"
        
        print(f"✅ Web検索成功: {len(search_results)}件の結果")
        
        # 検索結果を基に回答生成
        print("🤖 回答生成中...")
        llm = ChatBedrock(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            model_kwargs={"max_tokens": 500}
        )
        
        prompt = f"""以下のWeb検索結果を基に、質問に簡潔に回答してください。重要なポイントのみ含めてください。

{context}

質問: {query}"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "messages": [AIMessage(content=response.content)],
            "context": response.content
        }
        
    except Exception as e:
        print(f"❌ Web検索エラー: {str(e)}")
        return {
            "messages": [AIMessage(content=f"Web検索エラー: {str(e)}")],
            "context": f"Web検索エラー: {str(e)}"
        }

# Knowledge Baseエージェント
def knowledge_base_agent(state: State):
    """Knowledge Baseから関連情報を検索して回答します"""
    print('📚 Knowledge Baseエージェントが呼び出されました')
    
    query = state['query']
    
    # Bedrock Agent Runtimeクライアント
    kb_region = os.getenv('KNOWLEDGE_BASE_REGION', 'ap-northeast-1')
    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=kb_region)
    
    try:
        print(f"🔍 Knowledge Base ID: {os.getenv('KNOWLEDGE_BASE_ID')}")
        print(f"🔍 検索クエリ: {query}")
        
        # Knowledge Baseから検索
        try:
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
            print("🔄 ハイブリッド検索 + Amazon Rerank v1.0 使用")
        except Exception as rerank_error:
            print(f"⚠️ リランキングエラー: {rerank_error}")
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
            print("🔄 ハイブリッド検索使用")
        
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
            print("⚠️ Knowledge Baseに関連情報が見つかりません")
            return {
                "messages": [AIMessage(content="Knowledge Baseに関連する情報が見つかりませんでした。")],
                "context": "Knowledge Baseに関連する情報が見つかりませんでした。"
            }
        
        # 検索結果を基に回答生成
        print("🤖 回答生成中...")
        llm = ChatBedrock(
            # model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            model_kwargs={
                "temperature": 0.0,
                "max_tokens": 1024,
                "top_p": 0.1,
                "top_k": 1
            }
        )
        
        prompt = f"以下のKnowledge Baseの情報を基に、質問に簡潔に回答してください。\n\n{context}\n\n質問: {query}"
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "messages": [AIMessage(content=response.content)],
            "context": response.content
        }
        
    except Exception as e:
        print(f"❌ Knowledge Baseエラー: {str(e)}")
        return {
            "messages": [AIMessage(content=f"Knowledge Base検索エラー: {str(e)}")],
            "context": f"Knowledge Base検索エラー: {str(e)}"
        }

# AWSコスト管理エージェント
def aws_cost_agent(state: State):
    """AWSのコスト情報を取得して回答します"""
    print('💰 aws_cost_agent呼び出されました')
    
    query = state['query']
    
    try:
        # Cost Explorerクライアント
        cost_client = boto3.client('ce', region_name='us-east-1')  # Cost Explorerは us-east-1 のみ
        
        print(f"💰 コスト情報取得中: {query}")
        
        from datetime import datetime, timedelta
        
        # 過去30日間のコスト取得
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 日別コスト取得
        daily_cost_response = cost_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost']
        )
        
        # サービス別コスト取得
        service_cost_response = cost_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        # コスト情報を整理
        cost_info = "AWSコスト情報 (過去30日間):\n\n"
        
        # 総コスト計算
        total_cost = 0
        daily_costs = []
        for result in daily_cost_response['ResultsByTime']:
            daily_amount = float(result['Total']['BlendedCost']['Amount'])
            total_cost += daily_amount
            daily_costs.append({
                'date': result['TimePeriod']['Start'],
                'cost': daily_amount
            })
        
        cost_info += f"📊 総コスト: ${total_cost:.2f}\n"
        cost_info += f"📅 期間: {start_date} ～ {end_date}\n\n"
        
        # 最近5日間のコスト
        cost_info += "📈 最近5日間の日別コスト:\n"
        for daily in daily_costs[-5:]:
            cost_info += f"  {daily['date']}: ${daily['cost']:.2f}\n"
        cost_info += "\n"
        
        # サービス別コスト（上位5つ）
        cost_info += "🔧 サービス別コスト (上位5つ):\n"
        if service_cost_response['ResultsByTime']:
            groups = service_cost_response['ResultsByTime'][0]['Groups']
            # コスト順でソート
            sorted_services = sorted(groups, key=lambda x: float(x['Metrics']['BlendedCost']['Amount']), reverse=True)
            
            for i, service in enumerate(sorted_services[:5]):
                service_name = service['Keys'][0]
                service_cost = float(service['Metrics']['BlendedCost']['Amount'])
                cost_info += f"  {i+1}. {service_name}: ${service_cost:.2f}\n"
        
        print(f"✅ コスト情報取得成功")
        print(f"💰 総コスト: ${total_cost:.2f}")
        
        # コスト情報を基に回答生成
        print("🤖 コスト分析回答生成中...")
        llm = ChatBedrock(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            model_kwargs={
                "temperature": 0.0,
                "max_tokens": 1024
            }
        )
        
        prompt = f"""以下のAWSコスト情報を基に、ユーザーの質問に回答してください。コスト分析や節約提案も含めてください。

{cost_info}

質問: {query}"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "messages": [AIMessage(content=response.content)],
            "context": response.content
        }
        
    except Exception as e:
        print(f"❌ AWSコストエラー: {str(e)}")
        return {
            "messages": [AIMessage(content=f"AWSコスト取得エラー: {str(e)}")],
            "context": f"AWSコスト取得エラー: {str(e)}"
        }

# オーケストレーター（どのエージェントを使うか判断）
def orchestrator(state: State):
    """質問を分析して適切なエージェントを選択"""
    query = state['query']
    
    llm = ChatBedrock(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        model_kwargs={"max_tokens": 100}
    )
    
    prompt = f"""以下の質問を分析して、適切なエージェントを選択してください。

質問: {query}

選択肢:
- chat: 通常の回答
- web_search: Web検索が必要な最新情報の質問
- knowledge_base: ナレッジベースを使った回答（ジョジョの奇妙な冒険、AWS系の質問）
- aws_cost: AWSのコスト・料金・請求に関する質問

回答は「chat」、「web_search」、「knowledge_base」、または「aws_cost」のみで答えてください。"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    agent_type = response.content.strip().lower()
    
    if "knowledge_base" in agent_type:
        agent_type = "knowledge_base"
    elif "web_search" in agent_type:
        agent_type = "web_search"
    elif "aws_cost" in agent_type:
        agent_type = "aws_cost"
    else:
        agent_type = "chat"
    
    print(f"🎯 選択されたエージェント: {agent_type}")
    
    return {"agent_type": agent_type}

# 条件分岐関数
def route_agent(state: State):
    """エージェントタイプに基づいてルーティング"""
    if state["agent_type"] == "knowledge_base":
        return "knowledge_base_agent"
    elif state["agent_type"] == "web_search":
        return "web_search_agent"
    elif state["agent_type"] == "aws_cost":
        return "aws_cost_agent"
    else:
        return "chat_agent"

# グラフの構築
def create_graph():
    workflow = StateGraph(State)
    
    # ノードを追加（ノードとは、１つの作業を行う箱。関数を実行する場所。データを受け取って、処理して、結果を返すもの）
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("chat_agent", chat_agent)
    workflow.add_node("web_search_agent", web_search_agent)
    workflow.add_node("knowledge_base_agent", knowledge_base_agent)
    workflow.add_node("aws_cost_agent", aws_cost_agent)
    
    # エッジを追加（エッジとは、ノード間の道路・矢印。ノードからノードへの移動経路、実行順序を決める、データの流れを制御するもの）
    workflow.set_entry_point("orchestrator") # set_entry_pointでグラフ実行時に最初に実行されるノードを指定。必ず１つ指定する。
    workflow.add_conditional_edges(
        "orchestrator",
        route_agent,
        {
            "chat_agent": "chat_agent",
            "web_search_agent": "web_search_agent",
            "knowledge_base_agent": "knowledge_base_agent",
            "aws_cost_agent": "aws_cost_agent"
        }
    )
    workflow.add_edge("chat_agent", END)
    workflow.add_edge("web_search_agent", END)
    workflow.add_edge("knowledge_base_agent", END)
    workflow.add_edge("aws_cost_agent", END)
    
    return workflow.compile()

# レスポンス取得関数
def get_response(question: str):
    """質問に対する回答を取得"""
    graph = create_graph()
    
    result = graph.invoke({
        "messages": [],
        "query": question,
        "agent_type": "",
        "context": ""
    })
    
    return result["context"]

# インタラクティブチャット
if __name__ == "__main__":
    print("=== AI チャットボット (LangGraph版) ===")
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