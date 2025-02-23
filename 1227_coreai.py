import json
import boto3
from pprint import pprint

tool_name = "print_ai_analysis"
description = "与えられたテキストのAI分析結果を出力します。"

tool_definition = {
    "toolSpec": {
        "name": tool_name,
        "description": description,
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "youyaku": {
                        "type": "string",
                        "description": "全体の会話内容の要約を作成します。200文字程度にまとめてください。",
                    },
                    "hi-low-performance": {
                        "type": "number",
                        "description": "会話内容のoperatorの対応内容が、ハイパフォーマーだと思われる場合は1、ローパフォーマーだと思われる場合は2を返却します。",
                    },
                    "hi-low-reason": {
                        "type": "string",
                        "description": "ハイパフォーマーローパフォーマー判別した理由を、100文字程度にまとめまてください。",
                    },
                    "sentiment-all": {
                        "type": "string",
                        "description": "全体的なsentimentの状態を、positive,negative,neautralの3つのどれに当たるのかを返却してください。",
                    },
                    "csat": {
                        "type": "string",
                        "description": "会話全体の感情分析結果（ポジティブ、ネガティブ、ニュートラル）や要約内容から、顧客満足度スコア（1～10点）を推定し、スコアを返却してください。必ず1から10までの数値を返却してください。",
                    },
                },
                "required": ["youyaku", "hi-low-performance", "hi-low-reason", "sentiment-all", "csat"],
            }
        },
    }
}



# client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")
# model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# client = boto3.client("bedrock-runtime", region_name="us-east-1")
# model_id = "amazon.nova-lite-v1:0"

client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")
# model_id = "anthropic.claude-3-haiku-20240307-v1:0"
# model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
# MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"



def lambda_handler(event, context):

    try:
        # リクエストボディからデータを取得
        data = json.loads(event['body'])
        rows = data  # 受け取ったデータが直接行のリストとして扱われる

        # 感情分析結果を格納するリスト
        results = []

        for row in rows:
            index = row['index']       # ナンバリング
            timestamp = row['timestamp']
            speaker = row['speaker']   # スピーカー
            utterance = row['utterance']  # 発話
            sentiment = row['sentiment']
            # keywords = row['keywords']



            # # 感情分析を実施
            # response = comprehend.detect_sentiment(Text=utterance, LanguageCode='ja')  # 日本語の場合
            # sentiment = response['Sentiment']  # 感情分析の結果

            # # キーワード抽出を実施
            # keywords_response = comprehend.batch_detect_key_phrases(TextList=[utterance], LanguageCode='ja')
            # keywords = keywords_response['ResultList']  # キーワード抽出の結果
            
            # # キーワードを抽出してリストに格納
            # extracted_keywords = []
            # if keywords:  # 結果が存在する場合
            #     for keyword in keywords:
            #         for key_phrase in keyword['KeyPhrases']:
            #             extracted_keywords.append({
            #                 'Text': key_phrase['Text'],
            #                 'Score': key_phrase['Score'],
            #                 'BeginOffset': key_phrase['BeginOffset'],
            #                 'EndOffset': key_phrase['EndOffset']
            #             })
            
            
            
            
            
            # 結果を辞書にまとめる
            results.append({
                '#': index,
                'timestamp': timestamp,
                'speaker': speaker,
                'utterance': utterance,
                'sentiment': sentiment,
                # 'keywords': keywords
            })

        print(results)
        
        
        
        # results = '商品が届かないんですけど、どうなってるんですか？\n申し訳ございません。すぐにお調べいたします。\n調べてる間にもっと遅れたらどうするんですか？\nご安心ください。今すぐ担当部署に確認いたします。\n毎回こういうことが起きるのはなぜなんですか？\nこのたびの遅延、誠に申し訳ございません。\nこちらのミスですか？それとも配送業者ですか？\n現在、配送業者との連携状況を確認中です。\n何度もこんなことが起きるならもう使いたくない。\nそのお気持ちは理解しております。対策を強化いたします。'
        
                
        # results = '商品が届かないんですけど、どうなってるんですか？\n申し訳ございません。すぐにお調べいたします。'
        
        
        target_text = results
            
                
        prompt = f"""
        <text>
        {target_text}
        </text>

        {tool_name} ツールのみを利用すること。
        """


        inferenceConfig = ({"maxTokens": 4000, "temperature": 0})

        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ]
        
        
        # Send the message to the model
        response = client.converse(
            modelId=model_id,
            messages=messages,
            toolConfig={
                "tools": [tool_definition],
                "toolChoice": {
                    "tool": {
                        "name": tool_name,
                    },
                },
            },
            inferenceConfig=inferenceConfig
        )
        
        # pprint(response)
                
                
        print(response)



        # 結果をJSON形式で返す
        return {
            'isBase64Encoded': False,
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,GET',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'result': 'OK', 'results': response})  # 結果も含める
        }

    except Exception as e:
        # エラーが発生した場合の処理
        
        print(str(e))
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,GET',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': str(e),  # エラーメッセージを含める
                'message': '感情分析の処理中にエラーが発生しました。'
            }),
        }
