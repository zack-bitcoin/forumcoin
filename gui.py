import copy, tools, blockchain, custom, http, transactions
#the easiest way to understand this file is to try it out and have a look at 
#the html it creates. It creates a very simple page that allows you to spend 
#money.
def spend(amount, pubkey, privkey, to_pubkey, DB):
    amount=int(amount*(10**5))
    tx={'type':'spend', 'pubkeys':[pubkey], 'amount':amount, 'to':to_pubkey}
    easy_add_transaction(tx, privkey, DB)

def post(amount, pubkey, privkey, msg, parent, DB):
    amount=int(amount*(10**5))
    tx={'type':'post', 'pubkeys':[pubkey], 'amount':amount, 'msg':msg, 'parent':parent}
    easy_add_transaction(tx, privkey, DB)

def easy_add_transaction(tx_orig, privkey, DB):
    tx=copy.deepcopy(tx_orig)
    pubkey=tools.privtopub(privkey)
    address=tools.make_address([pubkey], 1)
    try:
        tx['count']=blockchain.count(address, DB)
    except:
        tx['count']=1
    tx['signatures']=[tools.sign(tools.det_hash(tx), privkey)]
    blockchain.add_tx(tx, DB)

submit_form='''
<form name="first" action="{}" method="{}">
<input type="submit" value="{}">{}
</form> {}
'''
empty_page='<html><body>{}</body></html>'

def easyForm(link, button_says, moreHtml='', typee='post'):
    a=submit_form.format(link, '{}', button_says, moreHtml, "{}")
    if typee=='get':
        return a.format('get', '{}')
    else:
        return a.format('post', '{}')

linkHome = easyForm('/', 'HOME', '', 'get')

def page1(DB, brainwallet=custom.brainwallet):
    out=empty_page
    txt='''<input type="text" name="BrainWallet" value="{}">
    <input type="hidden" name="location" value="root">
    '''
    out=out.format(easyForm('/home', 'Play Go!', txt.format(brainwallet)))
    return out.format('')

def home(DB, dic):
    if 'BrainWallet' in dic:
        dic['privkey']=tools.det_hash(dic['BrainWallet'])
    elif 'privkey' not in dic:
        return "<p>You didn't type in your brain wallet.</p>"
    privkey=dic['privkey']
    pubkey=tools.privtopub(dic['privkey'])
    address=tools.make_address([pubkey], 1)
    if 'do' in dic.keys():
        if dic['do']=='spend':
            spend(float(dic['amount']), pubkey, privkey, dic['to'], DB)
        if dic['do']=='post':
            post(float(dic['amount']), pubkey, privkey, dic['msg'], dic['parent'], DB)
    out=empty_page
    out=out.format('<p>your address: ' +str(address)+'</p>{}')
    out=out.format('<p>current block: ' +str(DB['length'])+'</p>{}')
    balance=blockchain.db_get(address, DB)['amount']
    for tx in DB['txs']:
        if tx['type'] == 'spend':
            if tx['to'] == address:
                balance += tx['amount']
            if tx['pubkeys'][0] == pubkey:
                balance -= tx['amount'] + custom.fee
        if tx['type'] == 'post':
            if tx['pubkeys'][0] == pubkey:
                balance -= tx['amount'] + custom.fee
    out=out.format('<p>current balance is: ' +str(balance/100000.0)+'</p>{}')
    if balance>0:
        out=out.format(easyForm('/home', 'spend money', '''
        <input type="hidden" name="location" value="{}">
        <input type="hidden" name="do" value="spend">
        <input type="text" name="to" value="address to give to">
        <input type="text" name="amount" value="amount to spend">
        <input type="hidden" name="privkey" value="{}">'''.format(dic['location'], privkey)))    
        out=out.format(easyForm('/home', 'create post', '''
        <input type="hidden" name="location" value="{}">
        <input type="hidden" name="do" value="post">
        <input type="text" name="msg" value="message">
        <input type="hidden" name="parent" value="{}">        
        <input type="text" name="amount" value="amount to spend">
        <input type="hidden" name="privkey" value="{}">'''.format(dic['location'], dic['location'], privkey)))
    #out=out.format('<p>'+str(DB['posts'])+'</p>{}')
    
    posts=map(lambda x: blockchain.db_get(x, DB), DB['posts'])
    zeroth_confirmations=filter(lambda tx: tx['type']=='post', DB['txs'])
    posts+=zeroth_confirmations
    def display_posts(posts, parent, tabs):
        out='{}'
        if tabs>3: return out
        for pos in posts:
            id_=transactions.postid(pos)
            if pos['parent']==parent:
                bumper='<div class="contentcontainer med left" style="margin-left: '+str(100*tabs)+'px;"><p>{}</p></div>'
                out=out.format(bumper.format(str(pos['msg']))+'{}')
                """
                out=out.format(easyForm('/home', 'comment', '''
                <input type="hidden" name="location" value="{}">
                <input type="hidden" name="do" value="post">
                <input type="text" name="msg" value="message">
                <input type="hidden" name="parent" value="{}">
                <input type="text" name="amount" value="amount to spend">
                <input type="hidden" name="privkey" value="{}">'''.format(dic['location'], id_, privkey)))
                """
                if not pos in zeroth_confirmations:
                    txt=bumper.format(easyForm('/home', 'focus', '''
                    <input type="hidden" name="location" value="{}">
                    <input type="hidden" name="parent" value="{}">
                    <input type="hidden" name="privkey" value="{}">'''.format(id_, id_,privkey))).format('')+'{}'
                    out=out.format(txt)
                out=out.format(display_posts(posts, id_, tabs+1))
        return out
    if dic['location']!='root':
        msg=blockchain.db_get(dic['location'], DB)
        print('msg: ' +str(msg))
        out=out.format('<h1>'+msg['msg']+'</h1>{}')
    out=out.format(display_posts(posts, dic['location'], 0))                
    txt='''    <input type="hidden" name="privkey" value="{}">
                <input type="hidden" name="location" value="{}">
'''.format(privkey, '{}')
    out=out.format(easyForm('/home', 'Current', txt.format(dic['location'])))
    s=easyForm('/home', 'Root', txt.format('root'))
    return out.format(s)

def hex2htmlPicture(string, size):
    txt='<img height="{}" src="data:image/png;base64,{}">{}'
    return txt.format(str(size), string, '{}')

def main(port, brain_wallet, db):
    global DB
    DB = db
    ip = ''
    http.server(DB, port, page1, home)
