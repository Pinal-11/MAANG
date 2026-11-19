# ----- Read Opration -------

# file = open("app.txt", "r")
# content = file.read()
# print(content)
# file.close()


#1st approch to get the whole content

# with open("app.txt", "r", encoding="utf-8") as f:
#     priread())             # It will print the whole content
#     print(f.rnt(f.eadline(), end="") # It will print only 1st line
#     print(f.readlines())        # It will print the whole content but in the list format

    # And one more important thing this all three command can't run in one shot so need to remove comment one by one 


# 2nd approch to get the content as this approch is used for the large file system
# with open("app.txt", "r", encoding="utf-8") as f:
#     for line in f:
#         # print(line.strip())
#         print(line, end="")
# print()

# -----------write Operation ---------------

with open("app2.txt", "w") as f:
    f.write("This is from the Write statement\n")

with open("app2.txt", "a") as f:
    f.write("This is the from the Append Statement\n")

with open("app2.txt", "r", encoding="utf-8") as f:
    for lines in f:
        print(lines.strip())
