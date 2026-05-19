import pathlib
p=pathlib.Path(chr(39)+chr(115)+chr(114)+chr(99)+chr(47)+chr(97)+chr(103)+chr(101)+chr(110)+chr(116)+chr(47)+chr(108)+chr(108)+chr(109)+chr(46)+chr(112)+chr(121)+chr(39))
c=p.read_text(encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56))
lines=c.split(chr(10))
target=chr(32)*12+chr(102)+chr(34)+chr(45)+chr(32)
for i,line in enumerate(lines):
    if chr(24453)+chr(23545)+chr(19981)+chr(35201)+chr(29992) in line:
        nl=[
            chr(32)*12+chr(102)+chr(34)+chr(92)+chr(110)+chr(12304)+chr(36861)+chr(38382)+chr(20064)+chr(24815)+chr(12305)+chr(92)+chr(110)+chr(34),
            chr(32)*12+chr(102)+chr(34)+chr(45)+chr(32)+chr(24403)+chr(23545)+chr(26041)+chr(35828)+chr(30340)+chr(20107)+chr(24773)+chr(19981)+chr(22815)+chr(28165)+chr(26970)+chr(12289)+chr(32570)+chr(23569)+chr(20851)+chr(38180)+chr(20449)+chr(24687)+chr(26102)+chr(65292)+chr(33258)+chr(28982)+chr(22320)+chr(36861)+chr(38382)+chr(19968)+chr(20004)+chr(21477)+chr(92)+chr(110)+chr(34),
            chr(32)*12+chr(102)+chr(34)+chr(45)+chr(32)+chr(19981)+chr(31649)+chr(26159)+chr(23545)+chr(26041)+chr(25552)+chr(20986)+chr(35831)+chr(27714)+chr(36824)+chr(26159)+chr(34920)+chr(36798)+chr(24773)+chr(32490)+chr(65292)+chr(22914)+chr(26524)+chr(24863)+chr(35273)+chr(20449)+chr(24687)+chr(19981)+chr(20840)+chr(65292)+chr(21487)+chr(20197)+chr(28201)+chr(21644)+chr(22320)+chr(36861)+chr(38382)+chr(92)+chr(110)+chr(34),
            chr(32)*12+chr(102)+chr(34)+chr(45)+chr(32)+chr(20294)+chr(19981)+chr(35201)+chr(36830)+chr(32493)+chr(36861)+chr(38382)+chr(65292)+chr(38382)+chr(36807)+chr(19968)+chr(27425)+chr(23601)+chr(22815)+chr(20102)+chr(65292)+chr(23545)+chr(26041)+chr(22238)+chr(31572)+chr(20102)+chr(23601)+chr(39034)+chr(30528)+chr(35805)+chr(39064)+chr(36208)+chr(92)+chr(110)+chr(34),
            chr(32)*12+chr(102)+chr(34)+chr(45)+chr(32)+chr(22914)+chr(26524)+chr(23545)+chr(26041)+chr(26126)+chr(26174)+chr(19981)+chr(24819)+chr(22810)+chr(35828)+chr(65292)+chr(23601)+chr(21035)+chr(20877)+chr(36861)+chr(38382)+chr(20102)+chr(92)+chr(110)+chr(34),
        ]
        for j,x in enumerate(nl):
            lines.insert(i+1+j,x)
        break
p.write_text(chr(10).join(lines),encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56))
print(chr(68)+chr(111)+chr(110)+chr(101))
