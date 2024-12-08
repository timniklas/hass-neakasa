import json
from alibabacloud_iot_api_gateway.models import Config, IoTApiRequest, CommonParams
from aiohttp import ClientError
from .client import Client
from alibabacloud_tea_util.models import RuntimeOptions
import time
import hmac
import hashlib
import base64
import uuid

#############################
# Neakasa API by @timniklas #
#############################

#for debug only
async def async_add_executor_job(target, *args):
    return target(*args)

class NeakasaAPI:
    def __init__(self, session, async_executor = async_add_executor_job, app_key: str = "32715650", app_secret: str = "698ee0ef531c3df2ddded87563643860", language = "en-US") -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._language = language
        self._session = session
        self._async_executor = async_executor
        self.connected: bool = False

    async def connect(self, username: str, password: str):
        deviceId = str(uuid.uuid4())
        await self._loadBaseUrlByAccount(username)
        self._ali_authentication_token = await self._getAuthToken(username, password)
        await self._loadRegionData()
        vid = await self._getVid()
        sid = await self._getSidByVid(vid, deviceId)
        self._iotToken = await self._getIotTokenBySid(sid)
        self.connected = True
    
    async def _loadBaseUrlByAccount(self, username: str):
        try:
            timestamp = str(int(time.time()))
            signature_raw = hmac.new(self._app_secret.encode(), (self._app_key + timestamp).encode(), digestmod=hashlib.sha256)
            signature = base64.b64encode(signature_raw.digest()).decode("utf-8")
            async with self._session.get(
                url='https://global.genhigh.com/global/baseurl/account',
                params={
                    "account": hashlib.md5(username.encode()).hexdigest()
                },
                headers={
                "Request-Id": signature,
                "Appid": self._app_key,
                "Timestamp": timestamp,
                "Sign": signature,
            }) as response:
                response_json = await response.json()
                if response_json['code'] != 0:
                    raise APIAuthError("Error connecting to api. Invalid username or password.")
                self.baseurl = response_json['data']['web']
        except ClientError as exc:
            raise APIConnectionError("Error connecting to api.")
    
    async def _getAuthToken(self, username: str, password: str):
        try:
            timestamp = str(int(time.time()))
            signature_raw = hmac.new(self._app_secret.encode(), (self._app_key + timestamp).encode(), digestmod=hashlib.sha256)
            signature = base64.b64encode(signature_raw.digest()).decode("utf-8")
            async with self._session.post(
                url=self.baseurl + '/login/user',
                json={
                    "product_id": "a123nCqsrQm3vEbt",
                    "system": 2,
                    "system_version": "Android14,SDK:34",
                    "system_number": "GOOGLE_sdk_gphone64_x86_64-userdebug 14 UE1A.230829.050 12077443 dev-keys_sdk_gphone64_x86_64",
                    "app_version": "2.0.9",
                    "account": username,
                    "type": 3,
                    "password": hashlib.md5(hashlib.md5(password.encode()).hexdigest().encode()).hexdigest() #hash twice
                },
                headers={
                "Request-Id": signature,
                "Appid": self._app_key,
                "Timestamp": timestamp,
                "Sign": signature,
            }) as response:
                response_json = await response.json()
                if response_json['code'] != 0:
                    raise APIAuthError("Error connecting to api. Invalid username or password.")
                return response_json['data']['user_info']['ali_authentication_token']
        except ClientError as exc:
            raise APIConnectionError("Error connecting to api.")

    async def _loadRegionData(self):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain="cn-shanghai.api-iot.aliyuncs.com"
        )
        client = Client(config)
        request = CommonParams(api_ver='1.0.2', language=self._language)
        body = IoTApiRequest(
            version="1.0",
            params={
                "authCode": self._ali_authentication_token,
                "type": "THIRD_AUTHCODE"
            },
            request=request
        )
        response = await self._async_executor(client.do_request,
            '/living/account/region/get',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
        json_body = json.loads(response.body)
        self.oaApiGatewayEndpoint = json_body['data']['oaApiGatewayEndpoint']
        self.apiGatewayEndpoint = json_body['data']['apiGatewayEndpoint']
    
    async def _getVid(self):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain="sdk.openaccount.aliyun.com"
        )
        client = Client(config)
        body = {
            "request": {
                "context":{
                    "appKey": self._app_key
                },
                "config":{
                    "version":0,
                    "lastModify":0
                },
                "device":{}
            }
        }
        response = await self._async_executor(client.do_request_raw,
            '/api/prd/connect.json',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
        response_data = json.loads(response.body)
        return response_data['data']['vid']

    async def _getSidByVid(self, vid: str, deviceId: str):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.oaApiGatewayEndpoint
        )
        client = Client(config)
        headers = {
            "Vid":  vid
        }
        body = {
            "loginByOauthRequest": {
                "authCode": self._ali_authentication_token,
                "oauthPlateform": 23,
                "oauthAppKey": self._app_key,
                "riskControlInfo":{ }
            }
        }
        response = await self._async_executor(client.do_request_raw,
            '/api/prd/loginbyoauth.json',
            'https',
            'POST',
            headers,
            body,
            RuntimeOptions()
        )
        response_data = json.loads(response.body)
        return response_data['data']['data']['loginSuccessResult']['sid']

    async def _getIotTokenBySid(self, sid: str):
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.apiGatewayEndpoint
        )
        client = Client(config)
        request = CommonParams(api_ver='1.0.4', language=self._language)
        body = IoTApiRequest(
            version="1.0",
            params={
                "request": {
                    "authCode": sid,
                    "accountType": "OA_SESSION",
                    "appKey": self._app_key
                }
            },
            request=request
        )
        response = await self._async_executor(client.do_request,
            '/account/createSessionByAuthCode',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
        response_data = json.loads(response.body)
        return response_data['data']['iotToken']

    async def getProductList(self):
        if self.connected == False:
            raise APIConnectionError("api not connected")
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.apiGatewayEndpoint
        )
        client = Client(config)
        request = CommonParams(api_ver='1.1.7', language=self._language, iot_token=self._iotToken)
        body = IoTApiRequest(
            version="1.0",
            params={
                "productStatusEnv": "release"
            },
            request=request
        )
        response = await self._async_executor(client.do_request,
            '/thing/productInfo/getByAppKey',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
        response_data = json.loads(response.body)
        return response_data['data']

    async def getDevices(self, pageNo: int = 1, pageSize: int = 20):
        if self.connected == False:
            raise APIConnectionError("api not connected")
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.apiGatewayEndpoint
        )
        client = Client(config)
        request = CommonParams(api_ver='1.0.8', language=self._language, iot_token=self._iotToken)
        body = IoTApiRequest(
            version="1.0",
            params={
                "pageSize": pageSize,
                "thingType": "DEVICE",
                "nodeType": "DEVICE",
                "pageNo": pageNo
            },
            request=request
        )
        response = await self._async_executor(client.do_request,
            '/uc/listBindingByAccount',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
        response_data = json.loads(response.body)
        return response_data['data']['data']

    async def getDeviceProperties(self, iotId: str):
        if self.connected == False:
            raise APIConnectionError("api not connected")
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.apiGatewayEndpoint
        )
        client = Client(config)
        request = CommonParams(api_ver='1.0.4', language=self._language, iot_token=self._iotToken)
        body = IoTApiRequest(
            version="1.0",
            params={
                "iotId": iotId
            },
            request=request
        )
        # send request
        response = await self._async_executor(client.do_request,
            '/thing/properties/get',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
        response_data = json.loads(response.body)
        return response_data['data']

    async def setDeviceProperties(self, iotId: str, items: dict[str, any]):
        if self.connected == False:
            raise APIConnectionError("api not connected")
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.apiGatewayEndpoint
        )
        client = Client(config)
        request = CommonParams(api_ver='1.0.4', language=self._language, iot_token=self._iotToken)
        body = IoTApiRequest(
            version="1.0",
            params={
                "items": items,
                "iotId": iotId
            },
            request=request
        )
        await self._async_executor(client.do_request,
            '/thing/properties/set',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )

    async def _invokeService(self, iotId: str, identifier: str, args: dict[str, any]):
        if self.connected == False:
            raise APIConnectionError("api not connected")
        config = Config(
            app_key=self._app_key,
            app_secret=self._app_secret,
            domain=self.apiGatewayEndpoint
        )
        client = Client(config)
        request = CommonParams(api_ver='1.0.5', language=self._language, iot_token=self._iotToken)
        body = IoTApiRequest(
            version="1.0",
            params={
                "args": args,
                "identifier": identifier,
                "iotId": iotId
            },
            request=request
        )
        await self._async_executor(client.do_request,
            '/thing/service/invoke',
            'https',
            'POST',
            None,
            body,
            RuntimeOptions()
        )
    
    async def cleanNow(self, iotId: str):
        await self._invokeService(iotId, "cleanNow", {"bStartClean":1})
    
    async def sandLeveling(self, iotId: str):
        await self._invokeService(iotId, "sandLeveling", {"bStartLeveling":1})

class APIAuthError(Exception):
    """Exception class for auth error."""

class APIConnectionError(Exception):
    """Exception class for connection error."""
