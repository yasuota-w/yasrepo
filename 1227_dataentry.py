import json
import boto3
import uuid
from datetime import datetime

# DynamoDBのリソースを作成
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # 受信データを解析
        data = json.loads(event['body'])
        agent_name = data['agent-name']
        talk = data['talk']
        summarize_text = data['summarize-text']
        hi_low_analysis = data['hi-low-analysis']
        all_sentiment = data['all-sentiment']
        csat = data['csat']
        hi_low_analysis = data['hi-low-analysis']
        
        # DynamoDBテーブル
        table_name = 'ISTT_NEXT'
        table = dynamodb.Table(table_name)

        # TENANT_NOの生成（5桁数値）
        tenant_no = '00000'

        # UUID_TIMESTAMPの生成
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        uuid_timestamp = f"{unique_id}-{timestamp}"

        # DynamoDBに登録するデータ
        item = {
            'TENANT_NO': tenant_no,
            'UUID_TIMESTAMP': uuid_timestamp,
            'AGENT_NAME': agent_name,
            'TALK': talk,
            'SUMMARIZE_TEXT': summarize_text,
            'HI_LOW_ANALYSIS': hi_low_analysis,
            'ALL_SENTIMENT': all_sentiment,
            'CSAT': csat,
            'HILOW': hilow
        }

        # データをDynamoDBに登録
        table.put_item(Item=item)

        print('OKです')

        return{
            'isBase64Encoded': False,
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, GET',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'result': 'OK'})
        }

    except Exception as e:
        # return {
        #     'statusCode': 500,
        #     'body': json.dumps({'error': str(e)})
        # }

        print('エラーです')
        print(str(e))

        return{
            'isBase64Encoded': False,
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, GET',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'result': 'ERROR'})
        }
