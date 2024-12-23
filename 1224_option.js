const in_claude3sonnet = 0.003;
const in_claude3haiku = 0.00025;
const in_novapro = 0.0008;
const in_novalite = 0.00006;

const out_claude3sonnet = 0.015;
const out_claude3haiku = 0.00125;
const out_novapro = 0.0032;
const out_novalite = 0.00024;



function calcCost(llmcmb, prompt_tokens, completion_tokens, total_tokens){
    let input_cost = 0;
    let output_cost = 0;
    let fKind = 0;

    if (llmcmb == 'ClaudeV3sonnet'){
        input_cost = in_claude3sonnet;
        output_cost = out_claude3sonnet;
    }

    if (llmcmb == 'ClaudeV3haiku'){
        input_cost = in_claude3haiku;
        output_cost = out_claude3haiku;
    }

    if (llmcmb == 'NovaPro'){
        input_cost = in_novapro;
        output_cost = out_novapro;
    }

    if (llmcmb == 'NovaLite'){
        input_cost = in_novalite;
        output_cost = out_novalite;
    }

    document.getElementById("tokenValue").textContent = Number(prompt_tokens);
    document.getElementById("tokenValueOutput").textContent = Number(completion_tokens);
    let sumtotal = document.getElementById("tokenValueTotal").textContent;
    document.getElementById("tokenValueTotal").textContent = Number(sumtotal) + Number(total_tokens);
    let tokencost = document.getElementById("tokenCost").textContent.slice(1);
    tokencost = Number(tokencost);

    let totalcost = Number(tokencost) + (Number(prompt_tokens)/1000 * Number(input_cost) + Number(completion_tokens)/1000 * Number(output_cost));
    document.getElementById("tokenCost").textContent = '$' + totalcost.toFixed(5);

    const apiurl = "https://012345678.execute-api.ap-northeast-1.amazonaws.com/dev/tokenrec";

    // var data = {
    //     "TOKENS_IN": prompt_tokens,
    //     "TOKENS_OUT": completion_tokens,
    //     "MAIL": 'varmail',
    //     "TENANT": "00000",
    //     "KIND": llmcmb,
    //     "FORM": ""
    // }

    // $.ajax({
    //     url: apiurl,
    //     type: 'POST',
    //     dataType: 'json',
    //     data: JSON.stringify(data)
    // })
    // .done(function(response){
    //     var item = "";
    //     item = response.Items;

    //     var data_json = JSON.parse(JSON.stringify(response));
    //     var result = data_json['data']['gpttext'];
    //     console.log(result);
    // })
    // .fail(function(jqXHR, textStatus, errorThrown){
    //     alert('コスト算出APIエラーです。');
    // })
}
