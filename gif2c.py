"""
gif2c

(c) 2018-2022 by Mathieu Brèthes (on github: https://github.com/mbrethes/gif2c)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as 
published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>. 

Based on code released in public domain by xiongyihui: https://gist.github.com/xiongyihui/1106c5755a966753ba2f02e827879aed


As input, uses a palletized image such as GIF or PNG.

v2
As output, generates 3 bitfields for each of the pic's shades.

v3
As output, generates 4 bitfields for each of the pic's shades.
if 0 : A B C D are lit
if 1 : A   C D are lit
if 2 :   B   D are lit
if 3 : A       is lit

v4
* When 2 pictures are the same, only store once in the file and put the same reference in the array.

v5
* accept multiple picture entries to generate a general C file that can cross-optimize stuff.
"""

import sys,hashlib
from PIL import Image

binaDict = {}

def makeBinary(f, im, name, rangeBeginX, rangeEndX, rangeBeginY, rangeEndY, colorSet):
    """
    This function generates binary C data for a frame.
    it uses md5 hash to check whether the frame is similar to a previously generated frame,
    if so, it returns the name of that frame.     
    otherwise it returns the name of the new frame.
    """
    farr = []
    for y in range(rangeBeginY, rangeEndY):
        val = "0b"
        valS = 0
        for x in range(rangeBeginX, rangeEndX):            
            if im.getpixel((x, y)) in colorSet:
                val = val + "1"
            else:
                val = val + "0"
            valS = valS + 1
                
            if valS == 8:
                farr.append(val + ", ")
                val = "0b"
                valS = 0
        if valS != 0:
            for valS in range(valS, 8):
                val = val + "0"
            farr.append(val + ", ")
        farr.append("\n")
        
    inStr = "".join(farr)
    
    m = hashlib.md5()
    m.update(inStr.encode('utf-8'))
    key = m.digest()
    if key in binaDict.keys():
        return binaDict[key]
    else:
        f.write('static const PROGMEM byte %s[] = {\n'%name)
        f.write(inStr)
        f.write('}; \n')
        binaDict[key] = name
        return name
    

def convertImage(f, imagename, dataname, anim_height, anim_width):
    """
    The general function to convert images.
    """

    im = Image.open(imagename)

    size = im.size
    
    if anim_height == 0:
        anim_height = size[1]
    if anim_width == 0:
        anim_width = size[0]

    if size[1] % anim_height != 0:
        print("Error : image size should be multiple of animation height.")
        sys.exit(2)
    
    if size[0] % anim_width != 0:
        print("Error : image size should be multiple of animation width.")
        sys.exit(3)

    # print((dataname, anim_height, anim_width))
    f.write('static const byte %s_x = %d;\n'%(dataname, anim_width))
    f.write('static const byte %s_y = %d;\n'%(dataname, anim_height))

    narrA = []
    narrB = []
    narrC = []
    narrD = []
    
    for animY in range(0, int(size[1] / anim_height)):
    
        for animX in range(0, int(size[0] / anim_width)):
    

            name = "%s_%d_%d_a"%(dataname, animX, animY)
            name = makeBinary(f, im, name, anim_width * animX, anim_width *(animX+1), anim_height * animY, anim_height * (animY + 1), (0, 1, 3))
            narrA.append(name)
        
            
            name = "%s_%d_%d_b"%(dataname, animX, animY)
            name = makeBinary(f, im, name, anim_width * animX, anim_width *(animX+1), anim_height * animY, anim_height * (animY + 1), (0, 2))
            narrB.append(name)

            name = "%s_%d_%d_c"%(dataname, animX, animY)
            name = makeBinary(f, im, name, anim_width * animX, anim_width *(animX+1), anim_height * animY, anim_height * (animY + 1), (0, 1))
            narrC.append(name)        

            name = "%s_%d_%d_d"%(dataname, animX, animY)
            name = makeBinary(f, im, name, anim_width * animX, anim_width *(animX+1), anim_height * animY, anim_height * (animY + 1), (0, 1, 2))
            narrD.append(name)                    
    
    f.write("static const int %s_alength = %d;\n"%(dataname,len(narrA)))
    
    f.write("static const PROGMEM byte* const %s_names_a[] = {\n"%dataname)
    f.write(", ".join(narrA))
    f.write("};\n")

    f.write("static const PROGMEM byte* const %s_names_b[] = {\n"%dataname)
    f.write(", ".join(narrB))
    f.write("};\n")
    
    f.write("static const PROGMEM byte* const %s_names_c[] = {\n"%dataname)
    f.write(", ".join(narrC))
    f.write("};\n")
    
    f.write("static const PROGMEM byte* const %s_names_d[] = {\n"%dataname)
    f.write(", ".join(narrD))
    f.write("};\n\n")
    
    im.close()
    

    

if len(sys.argv) < 4:
    print('Usage: python {} (image.gif/png dataname [h=anim_height *or* w=anim_width]) [image2.gif/.png dataname2 [h= / w=]] ... output.c'.format(sys.argv[0]))
    print('  [h=anim_height] : if set, cuts the image in slices of anim_height pixels (each becomes an independent image).')
    print('  [w=anim_width] : if set, cuts the image in slices of anim_width pixels.')
    print("  /!\ The program's function is undefined if both are set")
    sys.exit(1)

paramList = sys.argv

# on retire l'appel
paramList.pop(0)

cfile = paramList.pop()

if not cfile.endswith(".c"):
    print("Error : final parameter must be a C file name.")
    sys.exit(4)

f = open(cfile, "w")

paramArr = []
while True:
    try:
        imagename = paramList.pop(0)
        if not (imagename.endswith(".gif") or imagename.endswith(".png")):
            print("Error : image must be GIF or PNG (indexed colour)")
            sys.exit(5)
        dataname = paramList.pop(0)
        anim_height = 0
        anim_width = 0
        while True:
            try:
                option = paramList.pop(0)
                if option.startswith("h="):
                    anim_height = int(option[2:])
                elif option.startswith("w="):
                    anim_width = int(option[2:])
                else:
                    paramList.insert(0, option)
                    break
            except:
                break
        paramArr.append((imagename, dataname, anim_height, anim_width))        
    except:
        break

for infos in paramArr:
    # print(infos)
    convertImage(f,infos[0], infos[1], infos[2], infos[3])
    
f.close()
