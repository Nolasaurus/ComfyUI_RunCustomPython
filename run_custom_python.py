import torch
import ast
import inspect

class RunCustomPython:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"base_image": ("IMAGE",),
                             "python_script": ("STRING", {"default": "def process_image(image):\n    # Your custom code here (Note: images are in torch Tensor form)\n    return image", "multiline": True})}}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "run_custom_python_script"
    CATEGORY = "image"

    def run_custom_python_script(self, base_image, python_script):
        # Convert the image to CPU if it's on GPU
        base_image = base_image.cpu()

        # Parse the input string as Python code
        tree = ast.parse(python_script)

        # Find the function definition
        function_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'process_image':
                function_def = node
                break

        if function_def is None:
            raise ValueError("The python_script must contain a function named 'process_image'")

        # Compile and execute the function
        exec(compile(ast.Module(body=[function_def], type_ignores=[]), '<string>', 'exec'), globals())

        # Get the function from globals
        process_image = globals()['process_image']

        # Check if the function signature is correct
        sig = inspect.signature(process_image)
        if len(sig.parameters) != 1:
            raise ValueError("The process_image function must accept exactly one parameter")

        # Apply the function to the image
        new_image = process_image(base_image)

        # Ensure the output is a tensor
        if not isinstance(new_image, torch.Tensor):
            raise ValueError("The process_image function must return a torch.Tensor")

        # Move the result back to the original device
        new_image = new_image.to(base_image.device)

        return (new_image,)

NODE_CLASS_MAPPINGS = {
    "RunCustomPython": RunCustomPython,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RunCustomPython": "Run Custom Python Script",
}
