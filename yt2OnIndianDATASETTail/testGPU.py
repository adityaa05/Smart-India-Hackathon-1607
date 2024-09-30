import torch

def main():
    print("CUDA Available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("CUDA Device Name:", torch.cuda.get_device_name(0))
    else:
        print("CUDA is not available.")

if __name__ == "__main__":
    main()
