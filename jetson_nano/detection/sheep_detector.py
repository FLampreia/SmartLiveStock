# from jetson_nano.config.config_manager import get_value
#
# CONF_THRESHOLD = get_value("MIN_CONFIDENCE")
# MODEL_PATH = get_value("MODEL_PATH")
#
# print(f"Usando modelo: {MODEL_PATH} com confiança mínima: {CONF_THRESHOLD}")


from jetson_nano.config import get_static

model_path = get_static('detection','model_path')
device = get_static('resize','width')

print(model_path)
print(device)