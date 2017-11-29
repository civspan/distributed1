def writer():
    print("test1")
    files = ['/home/honk/skola/distributed1/skeleton/server/tst.html']
    html_page = ""
    for a_file in files:
        with open(a_file) as html_file:
            print(html_file.read())		
    print("test2")

if __name__ == "__main__":
    writer()
