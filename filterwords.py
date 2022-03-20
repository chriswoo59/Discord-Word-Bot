


with open("words.txt", "r") as f:
    words = f.read().splitlines()
    words.sort(key=len)   # Sort by length in ascending order
    print(words[:5])
    # Makes separate txt files containing words of length l
    for l in range(4,8):
        filtered = [w for w in words if len(w) == l and w.isalpha()]
        with open(f"words_length_{l}.txt", "w") as f:
            f.write('\n'.join(filtered))
        print(filtered[:5])

