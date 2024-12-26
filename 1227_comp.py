import json
import boto3
from datetime import datetime


def lambda_handler(event, context):
    # Comprehendのクライアントを作成
    comprehend = boto3.client('comprehend')

    try:
        # リクエストボディからデータを取得
        data = json.loads(event['body'])
        rows = data  # 受け取ったデータが直接行のリストとして扱われる

        # 感情分析結果を格納するリスト
        results = []

        for row in rows:
            # スピーカー、ナンバリング、発話を取得
            index = row['index']       # ナンバリング
            timestamp = row['timestamp']
            speaker = row['speaker']   # スピーカー
            utterance = row['utterance']  # 発話

            # フォーマットを指定してdatetimeオブジェクトに変換
            datetime_obj = datetime.strptime(timestamp.split(' GMT')[0], "%a %b %d %Y %H:%M:%S")

            # ISO 8601形式に変換
            iso_format_str = datetime_obj.isoformat(timespec='seconds') + "+09:00"

            # ISO 8601形式の日付文字列をdatetimeオブジェクトに変換
            dt = datetime.fromisoformat(iso_format_str)
            
            # 'YYYY-MM-DD HH:MM:SS'形式に変換して返す
            dt_now = dt.strftime('%Y-%m-%d %H:%M:%S')




            # 感情分析を実施
            response = comprehend.detect_sentiment(Text=utterance, LanguageCode='ja')  # 日本語の場合
            sentiment = response['Sentiment']  # 感情分析の結果

            # キーワード抽出を実施
            keywords_response = comprehend.batch_detect_key_phrases(TextList=[utterance], LanguageCode='ja')
            keywords = keywords_response['ResultList']  # キーワード抽出の結果
            
            # キーワードを抽出してリストに格納
            extracted_keywords = []
            if keywords:  # 結果が存在する場合
                for keyword in keywords:
                    for key_phrase in keyword['KeyPhrases']:
                        extracted_keywords.append({
                            'Text': key_phrase['Text'],
                            'Score': key_phrase['Score'],
                            'BeginOffset': key_phrase['BeginOffset'],
                            'EndOffset': key_phrase['EndOffset']
                        })
            
            
            # 結果を辞書にまとめる
            results.append({
                '#': index,
                'TIME': dt_now,
                'SPEAKER': speaker,
                'TEXT': utterance,
                'SENTIMENT': sentiment,
                'KEYWORDS': extracted_keywords
            })

        print(results)
        
        
        
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
            'body': json.dumps({'result': 'OK', 'results': results})  # 結果も含める
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
