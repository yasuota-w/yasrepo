#chatvector {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    overflow-y: auto;

    height: 600px;
    width: 100%;
    border: 1px solid #CCC;
}

#messages {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    overflow-y: auto;
    white-space: pre-wrap;
    width: 100%; /* 全幅に広げる */
    padding: 10px 10px; /* メッセージリスト全体に左右の余白を追加 */
}

#messages .message {
    display: flex;
    align-items: center; /* アイコンとテキストを縦中央揃え */
    padding: 10px;
    margin: 5px 0;
    border-radius: 5px; /* 四角形の角を少し丸める */
    text-align: left; /* 吹き出し内を左詰めに設定 */
}

#messages .message.left {
    justify-content: flex-start; /* 左揃え */
    background-color: #EEE;
    border: 1px solid #0084FF;
    color: black;
    font-size: 14px;
}

#messages .message.right {
    justify-content: flex-start; /* 右揃え */
    background-color: #0084FF;
    border: 1px solid #0084FF;
    color: #FFF;
    font-size: 14px;
}

/* アイコンを左端に固定 */
#messages .message::before {
    content: "";
    flex-shrink: 0; /* アイコンのサイズを固定 */
    display: inline-block;
    width: 40px;
    height: 40px;
    background-size: cover;
    background-position: center;
    border-radius: 50%;
    margin-right: 10px; /* アイコンとテキスト間のスペース */
    align-self: flex-start; /* アイコンを上部に配置 */
}

#messages .message.left::before {
    background-image: url("../img/chat-model.svg");
}

#messages .message.right::before {
    background-image: url("../img/chat-user-dark.svg");
}







#csvResultTable {
    border: 1px solid #CCC
}
