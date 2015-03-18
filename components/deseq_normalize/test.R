args<-commandArgs(TRUE)
A<-args[1]
B<-args[2]
THE_REST <- args[2:length(args)]

print(A)
print(B)
print(THE_REST)

for (item in THE_REST){
	print(item)
}
