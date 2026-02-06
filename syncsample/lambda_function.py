import boto3
import time

def lambda_handler(event, context):
    client = boto3.client('bedrock-agent')
    
    knowledge_base_id = ''
    data_source_id = ''
    
    # 同期開始
    print('同期を開始します...')
    start_response = client.start_ingestion_job(
        knowledgeBaseId=knowledge_base_id,
        dataSourceId=data_source_id
    )
    
    job_id = start_response['ingestionJob']['ingestionJobId']
    print(f'ジョブID: {job_id}')
    
    # 同期完了を待機
    while True:
        response = client.get_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            ingestionJobId=job_id
        )
        
        status = response['ingestionJob']['status']
        stats = response['ingestionJob'].get('statistics', {})
        scanned = stats.get('numberOfDocumentsScanned', 0)
        indexed = stats.get('numberOfNewDocumentsIndexed', 0) + stats.get('numberOfModifiedDocumentsIndexed', 0)
        
        print(f'ステータス: {status}, スキャン済み: {scanned}, インデックス済み: {indexed}')
        
        if status in ['COMPLETE', 'FAILED']:
            break
        
        time.sleep(10)
    
    # 結果を出力
    if status == 'COMPLETE':
        stats = response['ingestionJob']['statistics']
        indexed = stats.get('numberOfDocumentsScanned', 0)
        print(f'INDEXED: {indexed}')
        
        # ドキュメント一覧を取得
        print('\nドキュメント一覧を取得中...')
        doc_response = client.list_knowledge_base_documents(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            maxResults=100
        )
        
        documents = []
        for doc in doc_response.get('documentDetails', []):
            identifier = doc.get('identifier', {})
            if 's3' in identifier:
                uri = identifier['s3']['uri']
                doc_status = doc.get('status')
                print(f'  - {uri} (status: {doc_status})')
                documents.append({'uri': uri, 'status': doc_status})
        
        return {
            'statusCode': 200,
            'body': {
                'status': 'COMPLETE',
                'indexed': indexed,
                'statistics': stats,
                'documents': documents
            }
        }
    else:
        print('同期に失敗しました')
        return {
            'statusCode': 500,
            'body': {'status': 'FAILED'}
        }
