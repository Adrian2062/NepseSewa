import hmac
import hashlib
import base64

def generate_esewa_signature(secret_key, total_amount, transaction_uuid, product_code):
    """
    Generates SHA256 HMAC signature for eSewa ePay v2.
    Format: total_amount=VAL1,transaction_uuid=VAL2,product_code=VAL3
    """
    # eSewa v2 requires the literal keys AND values in the signature string
    msg = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    
    hash_obj = hmac.new(
        secret_key.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    )
    
    return base64.b64encode(hash_obj.digest()).decode('utf-8')
