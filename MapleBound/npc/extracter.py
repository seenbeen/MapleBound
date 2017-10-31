fout = open("data.txt","w")

lol = [[dat.split("=")[0]+" "+dat.split("=")[-1].strip("\"")
        for dat in  each.strip().strip("<i ").strip("/>").split()]
       for each in open("data.xml").readlines()][1:-1]

for each in lol:
    fout.write("\n".join([each[2],each[3],each[1],each[0]])+"\n")

fout.close()
