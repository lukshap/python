__author__ = 'Alesya'

class netString:

    def __init__(self, net_string):
        self.__ip_decimal = ''
        self.__ip_binary = ''
        self.__mask_decimal = ''
        self.__mask_binary = ''
        self.__network_binary = ''
        self.__network_decimal = ''
        self.__broadcast_binary = ''
        self.__broadcast_decimal = ''

        self.set_ip_decimal(net_string)
        self.set_mask_decimal(net_string)
        self.set_ip_binary(net_string)
        self.set_mask_binary(net_string)
        self.set_network_binary()
        self.set_network_decimal()
        self.set_broadcast_binary()
        self.set_broadcast_decimal()

    def __str__(self):
        return "ip_decimal:{0}; ip_binary:{1}; mask_decimal:{2}; mask_binary:{3}; network_decimal:{4}; network_binary:{5}; broadcast_decimal:{6}; broadcast_binary:{7}".format(self.__ip_decimal, self.__ip_binary, self.__mask_decimal, self.__mask_binary, self.__network_decimal, self.__network_binary, self.__broadcast_decimal, self.__broadcast_binary)

    def get_ip_decimal(self):
        return self.__ip_decimal

    def get_ip_binary(self):
        return self.__ip_binary

    def get_mask_decimal(self):
        return self.__mask_decimal

    def get_mask_binary(self):
        return self.__mask_binary

    def get_network_decimal(self):
        return self.__network_decimal

    def get_network_binary(self):
        return self.__network_binary

    def get_broadcast_decimal(self):
        return self.__broadcast_decimal

    def get_broadcast_binary(self):
        return self.__broadcast_binary

    def set_ip_decimal(self, net_string):
        l=net_string.split('/')
        self.__ip_decimal = l[0]

    def set_ip_binary(self, net_string):
        self.__ip_binary = ''
        l=net_string.split('/')
        ip_decimal = l[0]
        self.__ip_binary = self.convert_to_binary(ip_decimal)

    def set_mask_decimal(self, net_string):
        self.__mask_decimal = ''
        l=net_string.split('/')
        count_1=int(l[1])
        l.clear()
        mask_binary = '1'*count_1+'0'*(32-count_1)
        self.__mask_decimal = self.convert_to_decimal(mask_binary)

    def set_mask_binary(self, net_string):
        l=net_string.split('/')
        count_1=int(l[1])
        self.__mask_binary = '1'*count_1+'0'*(32-count_1)

    def set_network_binary(self):
        self.__network_binary = self.bit_multiply(self.__ip_binary, self.__mask_binary)

    def set_network_decimal(self):
        self.__network_decimal = self.convert_to_decimal(self.__network_binary)

    def set_broadcast_decimal(self):
        self.__broadcast_decimal = self.convert_to_decimal(self.__broadcast_binary)

    def set_broadcast_binary(self):
        self.__broadcast_binary = self.bit_addition(self.__network_binary, self.get_invert_mask(self.__mask_binary))

    ip_decimal = property(get_ip_decimal, set_ip_decimal)
    ip_binary = property(get_ip_binary, set_ip_binary)
    mask_decimal = property(get_mask_decimal, set_mask_decimal)
    mask_binary = property(get_mask_binary, set_mask_binary)
    network_decimal = property(get_network_decimal, set_network_decimal)
    network_binary = property(get_network_binary, set_network_binary)
    broadcast_decimal = property(get_broadcast_decimal, set_broadcast_decimal)
    broadcast_binary = property(get_broadcast_binary, set_broadcast_binary)

    def from_decimal_to_binary(self,num):
        num = int(num)
        bin_num = ''
        while num>0 or len(bin_num)<8:
            if not num>0:
                bin_num='0'+bin_num
                continue
            y = str(num%2)
            bin_num = y+bin_num
            num = int(num/2)
        return bin_num

    def from_binary_to_decimal(self, bin_num):
        bin_num = str(bin_num)
        while bin_num[0]=='0':
             bin_num = bin_num[1:]

        n=len(bin_num)
        num=0
        for i in range(0,n):
            if not bin_num[i]=='0':
                num+=2**(n-i-1)
        return str(num)

    def convert_to_binary(self, net_dec):
        net_bin = ''
        l=net_dec.split('.')
        num_bin=''
        for i in l:
            num_bin = self.from_decimal_to_binary(i)
            net_bin+=num_bin
        return net_bin

    def convert_to_decimal(self,net_bin):
        net_dec=''
        l=[]
        for i in range (0,4):
            num = self.from_binary_to_decimal(net_bin[8*i:8*(i+1)])
            l.append(num)
        net_dec='.'.join(l)
        return net_dec

    def get_invert_mask(self, mask_binary):
        mask_invert_binary=''
        for i in range(0,32):
            if mask_binary[i]=='1':
                mask_invert_binary+='0'
            else: mask_invert_binary+='1'
        return mask_invert_binary

    def bit_multiply(self, ip_binary, mask_binary):
        network_binary=''
        for i in range(0,32):
            if ip_binary[i]=='1' and mask_binary[i]=='1':
                network_binary+='1'
            else: network_binary+='0'
        return network_binary

    def bit_addition(self, network_binary, mask_invert_binary):
        broadcast_binary = ''
        for i in range(0,32):
            if network_binary[i]=='0' and mask_invert_binary[i]=='0':
                broadcast_binary+='0'
            else: broadcast_binary+='1'
        return broadcast_binary

a=netString("192.168.64.95/26")
print(a.ip_decimal)
print(a.ip_binary)
print(a.mask_binary)
print(a.mask_decimal)

print(a.network_binary)
print(a.network_decimal)
print(a.broadcast_binary)
print(a.broadcast_decimal)

