import os
import jwt
import requests
from typing import Dict, Optional
from cryptography.hazmat.primitives import serialization


class VerifyToken:
    def __init__(self):
        self.AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
        self.AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
        self.AUTH0_ISSUER = os.getenv("AUTH0_ISSUER")
        self.AUTH0_ALGORITHMS = os.getenv("AUTH0_ALGORITHMS")
        
        if not all([self.AUTH0_DOMAIN, self.AUTH0_API_AUDIENCE, self.AUTH0_ISSUER, self.AUTH0_ALGORITHMS]):
            raise ValueError("Auth0 environment variables are not properly configured")
        
        self._jwks_cache = None
    
    def _get_jwks(self) -> Dict:
        if self._jwks_cache is None:
            jwks_url = f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"
            response = requests.get(jwks_url)
            response.raise_for_status()
            self._jwks_cache = response.json()
        return self._jwks_cache
    
    def _get_signing_key(self, token: str) -> str:
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise ValueError("Invalid token header")
        
        kid = unverified_header.get("kid")
        if not kid:
            raise ValueError("Token header missing 'kid' claim")
        
        jwks = self._get_jwks()
        for key in jwks["keys"]:
            if key["kid"] == kid:
                # Convert JWK to PEM format using PyJWT's RSAAlgorithm
                rsa_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                # rsa_key is already a public key object
                key_pem = rsa_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                return key_pem.decode()
        
        raise ValueError("Unable to find appropriate signing key")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            signing_key = self._get_signing_key(token)
            
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[self.AUTH0_ALGORITHMS],
                audience=self.AUTH0_API_AUDIENCE,
                issuer=self.AUTH0_ISSUER
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")