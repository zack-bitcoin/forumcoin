import blockchain, custom, copy, tools
#This file explains how we tell if a transaction is valid or not, it explains 
#how we update the system when new transactions are added to the blockchain.
def addr(tx): return tools.make_address(tx['pubkeys'], len(tx['signatures']))

def postid(tx): 
    return tools.det_hash({'msg':tx['msg'], 'parent':tx['parent']})

def enough_coins(tx, txs, DB):
    address=addr(tx)
    total_cost=0
    for Tx in filter(lambda t: address==addr(t), [tx]+txs):
        if Tx['type'] in ['spend', 'post', 'reputation']:
            total_cost+=Tx['amount']
        if Tx['type']=='mint':
            total_cost-=custom.block_reward
    return int(blockchain.db_get(address, DB)['amount'])>=total_cost+custom.fee

def signatures_check(tx, txs, DB):    

    def sigs_match(sigs, pubs, msg):
        for sig in sigs:
            for pub in pubs:
                try:
                    if tools.verify(msg, sig, pub):
                        sigs.remove(sig)
                        pubs.remove(pub)
                except:
                    pass
        return len(sigs)==0

    tx_copy=copy.deepcopy(tx)
    tx_copy_2=copy.deepcopy(tx)
    tx_copy.pop('signatures')
    if len(tx['pubkeys'])==0: return False
    if len(tx['signatures'])>len(tx['pubkeys']): return False
    msg=tools.det_hash(tx_copy)
    if not sigs_match(copy.deepcopy(tx['signatures']), copy.deepcopy(tx['pubkeys']), msg): return False
    return True

def spend_verify(tx, txs, DB): 
    if not signatures_check(tx, txs, DB): return False
    return enough_coins(tx, txs, DB)

def mint_verify(tx, txs, DB): 
    return 0==len(filter(lambda t: t['type']=='mint', txs))

def post_verify(tx, txs, DB):
    id_=postid(tx)
    for i in DB['db'].RangeIter():
        if i[0]==id_:
            return False
    if len(tx['msg'])>500: return False
    if not signatures_check(tx, txs, DB): return False
    return spend_verify(tx, txs, DB)

def reputation_verify(tx, txs, DB):
    if not signatures_check(tx, txs, DB): return False
    return enough_coins(tx, txs, DB)
tx_check={'spend':spend_verify, 'mint':mint_verify, 'post':post_verify, 'reputation':reputation_verify}####
#------------------------------------------------------

def adjust(key, pubkey, amount, DB):
    acc=blockchain.db_get(pubkey, DB)
    acc[key]+=amount
    blockchain.db_put(pubkey, acc, DB)

def mint(tx, DB): 
    address=addr(tx)
    adjust('amount', address, custom.block_reward, DB)
    adjust('count', address, 1, DB)

def spend(tx, DB):
    address=addr(tx)
    adjust('amount', address, -tx['amount']-custom.fee, DB)
    adjust('amount', tx['to'], tx['amount'], DB)
    adjust('count', address, 1, DB)

def post(tx, DB):
    address=addr(tx)
    adjust('amount', address, -tx['amount']-custom.fee, DB)
    adjust('count', address, 1, DB)
    post={'amount':tx['amount'], 'msg':tx['msg'], 'parent':tx['parent'], 'children':[]}
    id_=postid(post)
    DB['posts'].append(id_)
    blockchain.db_put(id_, post, DB) 
    
def reputation(tx, DB):
    address=addr(tx)
    adjust('amount', address, -tx['amount']-custom.fee, DB)
    adjust('reputation', tx['to'], tx['amount'], DB)
    adjust('count', address, 1, DB)

add_block={'mint':mint, 'spend':spend, 'post':post, 'reputation':reputation}####
#-----------------------------------------

def unmint(tx, DB):
    address=addr(tx)
    adjust('amount', address, -custom.block_reward, DB)
    adjust('count', address, -1, DB)
    
def unspend(tx, DB):
    address=addr(tx)
    adjust('amount', address, custom.fee+tx['amount'], DB)
    adjust('amount', tx['to'], -tx['amount'], DB)
    adjust('count', address, -1, DB)

def unpost(tx, DB):
    address=addr(tx)
    adjust('amount', address, tx['amount']+custom.fee, DB)
    adjust('count', address, -1, DB)
    post={'amount':tx['amount'], 'msg':tx['msg'], 'parent':tx['parent'], 'children':[]}
    id_=postid(post)
    DB['posts'].remove(id_)
    blockchain.db_delete(id_, DB) 

def unreputation(tx, DB):
    address=addr(tx)
    adjust('amount', address, tx['amount']+custom.fee, DB)
    adjust('reputation', tx['to'], -tx['amount'], DB)
    adjust('count', address, -1, DB)
    
delete_block={'mint':unmint, 'spend':unspend, 'post':unpost, 'reputation':unreputation}####
#------------------------------------------------
