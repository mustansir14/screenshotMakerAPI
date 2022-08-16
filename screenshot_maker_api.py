from importlib.metadata import requires
from flask import Flask, request
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from config import *
from pyvirtualdisplay import Display
import logging, os, zipfile
from webdriver_manager.chrome import ChromeDriverManager
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)

api = Flask(__name__)

@api.route('/api/v1/screenshot', methods=['GET'])
def get_screenshot():

    if "url" not in request.args:
        return {"status": "error", "message": "missing url argument"}, 400

    options = Options()
    options.add_argument("--log-level=3")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--renderer-process-limit=1'); # do not allow take more resources
    options.add_argument('--disable-crash-reporter'); # disable crash reporter process
    options.add_argument('--no-zygote'); # disable zygote process
    options.add_argument('--disable-crashpad')
    options.add_argument('--screenshot-maker-mustansir')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36")
    if "useProxy" in request.args and int(request.args["useProxy"]):
        if PROXY_USER and PROXY_PASS:
            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "%s",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (PROXY_TYPE, PROXY, PROXY_PORT, PROXY_USER, PROXY_PASS)
            pluginfile = 'temp/proxy_auth_plugin.zip'
            if not os.path.isdir("temp"):
                os.mkdir("temp")
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            options.add_extension(pluginfile)

            display = Display(visible=0, size=(1920, 1080))
            display.start()
        else:
            options.add_argument("--proxy-server=%s" % PROXY_TYPE + "://" + PROXY + ":" + PROXY_PORT)
    else:
        options.headless = True

    driver = Chrome(options=options, executable_path=ChromeDriverManager().install())
    
    try:
        driver.get(request.args['url'])
    except:
        driver.quit()
        if "useProxy" in request.args and PROXY_USER and PROXY_PASS:
            display.stop()
        return {"status": "error", "message": "Invalid URL"}, 400
    
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    image = driver.get_screenshot_as_base64()
    driver.quit()
    if "useProxy" in request.args and PROXY_USER and PROXY_PASS:
        display.stop()
    return {"status": "success", "imageBase64": image, "imageWidth": required_width, "imageHeight": required_height}, 200


if __name__ == "__main__":
    api.run()
