import yaml
import json

# packaged.yamlの読み込み
with open('packaged.yaml', 'r') as file:
    packaged_yaml = yaml.safe_load(file)

resources_to_import = []

# リソースの情報を抽出
for resource_name, resource in packaged_yaml['Resources'].items():
    if resource['Type'] == 'AWS::Serverless::Function':
        logical_id = resource_name
        # Fn::Subの式からFunctionNameを抽出
        function_name_template = resource['Properties']['FunctionName']['Fn::Sub']
        
        # `${EnvType}`の部分を置換して、具体的なFunctionNameを得る（例: GPT-test-dev）
        function_name = function_name_template.replace('${EnvType}', 'dev')  # 'dev'を使って最終的な名前を作成
        
        resource_info = {
            "ResourceType": "AWS::Lambda::Function",
            "LogicalResourceId": logical_id,
            "ResourceIdentifier": {
                "FunctionName": function_name
            }
        }
        resources_to_import.append(resource_info)

# 生成するコマンドの組み立て
resources_to_import_json = json.dumps(resources_to_import, indent=2)

change_set_command = f"""
aws cloudformation create-change-set \\
  --stack-name STACK-LAMBDA-TEST \\
  --change-set-name ImportExistingLambdaFunction20241215 \\
  --change-set-type IMPORT \\
  --resources-to-import '{resources_to_import_json}' \\
  --template-body file://packaged.yaml \\
  --capabilities CAPABILITY_IAM
"""

# 出力ファイルのパス
output_file = 'generated_command.txt'

# コマンドをファイルに保存
with open(output_file, 'w') as file:
    file.write(change_set_command)

print(f"コマンドが '{output_file}' に保存されました。")
