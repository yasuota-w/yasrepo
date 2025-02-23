import json
import os
import re
import shutil
import base64

import boto3

s3_client = boto3.client('s3')


def lambda_handler(event, context):

    try:
        data = json.loads(event['body'])
        target_text = data['targettext']
        talk_history = data['talkhistory']
        tenant_no = '00000'
        llm_cmb = data['llmcmb']
        system_role = data['sysrole']

        p_max_tokens = '4096'
        p_temp = '0'
        p_rep = '0'

        if llm_cmb == 'NovaPro' or llm_cmb == 'NovaLite':
            bedrock_runtime = boto3.client('bedrock-runtime', region_name = 'us-east-1')

            if llm_cmb == 'NovaPro':
                model_id = 'amazon.nova-pro-v1:0'

            elif llm_cmb == 'NovaLite':
                model_id = 'amazon.nova-lite-v1:0'

        elif llm_cmb == 'ClaudeV3sonnet' or llm_cmb == 'ClaudeV3haiku':
            bedrock_runtime = boto3.client('bedrock-runtime', region_name = 'us-west-2')

            if llm_cmb == 'ClaudeV3sonnet':
                model_id = 'anthropic.claude-3-5-sonnet-20241022-v2:0'

            elif llm_cmb == 'ClaudeV3haiku':
                model_id = 'anthropic.claude-3-haiku-20240307-v1:0'

        system = [{'text': f'{system_role}'}]
        prompt = []


        # # 最新のn件だけに絞り込む
        # # userから始まらないとエラーになるらしいのでコメントアウト
        # n = 100
        # if len(talk_history) > n:
        #     talk_history = talk_history[-n:]

        for message in talk_history:
            role = 'assistant' if message[1] == 'left' else 'user'
            content_list = []

            if role == 'user' and message[3]:
                base64_data = message[3].split(',',1)[1] if ',' in message[3] else message[3]
                # media_type = message[3].split(';')[0].split(':')[1] if ';' in message[3] and ':' in message[3]
                media_type = message[3].split(';')[0].split(':')[1] if ';' in message[3] and ':' in message[3] else None


                media_type = media_type.replace('image/', '')

                if base64_data:
                    image_data = base64.b64decode(base64_data)

                    content_list.append(
                        {'image': {
                            'format': media_type,
                            'source': {'bytes': image_data}
                        }}
                    )

            content_list.append({
                'text': message[0]
            })

            prompt.append({
                'role': role,
                'content': content_list
            })

            inference_config = {
                'maxTokens': int(p_max_tokens),
                'temperature': float(p_temp),
                'topP': float(p_rep),
            }

        print('prompt is...')
        print(prompt)

        print('system is...')
        print(system)

        response = bedrock_runtime.converse (
            modelId = model_id,
            messages = prompt,
            inferenceConfig = inference_config,
            system = system
        )

        answer = response['output']['message']['content'][0]['text']
        tokens_count = response['usage']['inputTokens']
        tokens_count_output = response['usage']['outputTokens']
        totaltoken = response['usage']['totalTokens']

        jsn = {
            'data': {
                'gpttext': answer,
                'prompt_tokens': tokens_count,
                'completion_tokens': tokens_count_output,
                'total_tokens': totaltoken,
                'nodeused': 'nodeused',
                'nodetext': 'nodetext'
            }
        }

        print('API返却値')
        print(jsn)

        return {
            'isBase64Encoded': False,
            'statusCode': '200',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,GET',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(jsn)
        }

    except Exception as e:
        # エラーの詳細をログに出力
        print(f"Error: {str(e)}")
        
        jsn = {
            'data': {'gpttext': 'API error'}
        }

        return {
            'isBase64Encoded': False,
            'statusCode': '500',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,GET',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(jsn)
        }
