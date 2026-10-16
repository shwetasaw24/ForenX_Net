from services.forenxnet_pipeline import ForenXNetPipeline

pipeline = ForenXNetPipeline()

image_path = "data/input/test_image.jpeg"

result = pipeline.analyze(image_path)

print("\n========== SCI RESULT ==========")
print(result["source_camera"])

print("\n========== FORGERY CLASSIFICATION ==========")
print(result["forgery_classification"])
