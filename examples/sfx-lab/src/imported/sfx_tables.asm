****************************************
* CoCoIDE 6809 disassembly (best-effort)
* Aimed at lwasm: labels + indented ops
* Data-as-code may still need hand cleanup
****************************************

	org	$0000
* raw binary (not DECB LOADM)
* External / out-of-segment targets (ROM, RAM, etc.)
L0C81	equ	$0C81
L0CC0	equ	$0CC0
L1871	equ	$1871
L1975	equ	$1975
L1979	equ	$1979

L0000
	swi
L0001
	swi
L0002
	swi
L0003
	swi
L0004
	swi
L0005
	swi
L0006
	swi
L0007
	swi
L0008
	swi
L0009
	swi
L000A
	swi
L000B
	swi
L000C
	swi
L000D
	swi
L000E
	swi
L000F
	swi
L0010
	swi
L0011
	swi
L0012
	swi
L0013
	swi
L0014
	swi
L0015
	swi
L0016
	swi
L0017
	swi
L0018
	swi
L0019
	swi
L001A
	swi
L001B
	swi
L001C
	swi
L001D
	swi
L001E
	swi
L001F
	swi
L0020
	swi
L0021
	swi
L0022
	swi
L0023
	swi
L0024
	swi
L0025
	swi
L0026
	swi
L0027
	swi
L0028
	swi
L0029
	swi
L002A
	swi
L002B
	swi
L002C
	swi
L002D
	swi
L002E
	swi
L002F
	swi
L0030
	swi
L0031
	swi
L0032
	swi
L0033
	swi
L0034
	swi
L0035
	swi
L0036
	swi
L0037
	swi
L0038
	swi
L0039
	swi
L003A
	swi
L003B
	swi
L003C
	swi
L003D
	swi
L003E
	swi
L003F
	swi
L0040
	swi
L0041
	swi
L0042
	swi
L0043
	swi
L0044
	swi
L0045
	swi
L0046
	swi
L0047
	swi
L0048
	swi
L0049
	swi
L004A
	swi
L004B
	swi
L004C
	swi
L004D
	swi
L004E
	swi
L004F
	swi
L0050
	swi
L0051
	swi
L0052
	swi
L0053
	swi
L0054
	swi
L0055
	swi
L0056
	swi
L0057
	swi
L0058
	swi
L0059
	swi
L005A
	swi
L005B
	swi
L005C
	swi
L005D
	swi
L005E
	swi
L005F
	swi
L0060
	swi
L0061
	swi
L0062
	swi
L0063
	swi
L0064
	swi
L0065
	swi
L0066
	swi
L0067
	swi
L0068
	swi
L0069
	swi
L006A
	swi
L006B
	swi
L006C
	swi
L006D
	swi
L006E
	swi
L006F
	swi
L0070
	swi
L0071
	swi
L0072
	swi
L0073
	swi
L0074
	swi
L0075
	swi
L0076
	swi
L0077
	swi
L0078
	swi
L0079
	swi
L007A
	swi
L007B
	swi
L007C
	swi
L007D
	swi
L007E
	swi
L007F
	swi
L0080
	neg <$00
L0082
	neg <$00
L0084
	neg <$00
L0086
	neg <$00
L0088
	neg <$00
L008A
	neg <$00
L008C
	neg <$00
L008E
	neg <$00
L0090
	neg <$00
L0092
	neg <$00
L0094
	neg <$00
L0096
	neg <$00
L0098
	neg <$00
L009A
	neg <$00
L009C
	neg <$00
L009E
	neg <$00
L00A0
	neg <$00
L00A2
	neg <$00
L00A4
	neg <$00
L00A6
	neg <$00
L00A8
	neg <$00
L00AA
	neg <$00
L00AC
	neg <$00
L00AE
	neg <$00
L00B0
	neg <$00
L00B2
	neg <$00
L00B4
	neg <$00
L00B6
	neg <$00
L00B8
	neg <$00
L00BA
	neg <$00
L00BC
	neg <$00
L00BE
	neg <$00
L00C0
	neg <$00
L00C2
	neg <$00
L00C4
	neg <$00
L00C6
	neg <$00
L00C8
	neg <$00
L00CA
	neg <$00
L00CC
	neg <$00
L00CE
	neg <$00
L00D0
	neg <$00
L00D2
	neg <$00
L00D4
	neg <$00
L00D6
	neg <$00
L00D8
	neg <$00
L00DA
	neg <$00
L00DC
	neg <$00
L00DE
	neg <$00
L00E0
	neg <$00
L00E2
	neg <$00
L00E4
	neg <$00
L00E6
	neg <$00
L00E8
	neg <$00
L00EA
	neg <$00
L00EC
	neg <$00
L00EE
	neg <$00
L00F0
	neg <$00
L00F2
	neg <$00
L00F4
	neg <$00
L00F6
	neg <$00
L00F8
	neg <$00
L00FA
	neg <$00
L00FC
	neg <$00
L00FE
	neg <$00
L0100
	leax -8,Y
L0102
	andcc #$0E
L0104
	beq L0139
L0106
	daa
L0107
	bge L011F
L0109
	bmi L0120
L010B
	bpl L0122
L010D
	dec <$05
L010F
	bhi L0122
L0111
	asl <$24
L0113
	leas -7,Y
L0115
	andcc #$0E
L0117
	asr <$23
L0119
	fcb $11,$28
L011B
	pshs A,DP,X,Y
L011D
	sex
L011E
	fcb $2E
L011F
	fcb $37
L0120
	fcb $1B
L0121
	fcb $0D
L0122
	ror <$03
L0124
	brn L0136
L0126
	asl <$04
L0128
	bhi L015B
L012A
	fcb $38
L012B
	andcc #$2E
L012D
	pulu CC,A,DP,X,Y
L012F
	sex
L0130
	jmp <$27
L0132
	leau -7,Y
L0134
	andcc #$0E
L0136
	asr <$23
L0138
	fcb $31
L0139
	fcb $38
L013A
	cwai #$1E
L013C
	ble L0155
L013E
	bmi L0155
L0140
	dec <$05
L0142
	fcb $02
L0143
	fcb $01
L0144
	neg <$20
L0146
	fcb $10,$08
L0148
	lsr <$22
L014A
	fcb $11,$28
L014C
	fcb $14
L014D
	dec <$25
L014F
	nop
L0150
	bvs L0166
L0152
	bpl L0189
L0154
	abx
L0155
	mul
L0156
	fcb $1E
L0157
	ble L0190
L0159
	rti
L015A
	sex
L015B
	bgt L0194
L015D
	fcb $1B
L015E
	blt L0176
L0160
	fcb $0B
L0161
	fcb $05
L0162
	fcb $02
L0163
	brn L0195
L0165
	fcb $38
L0166
	cwai #$3E
L0168
	tfr D,$F
L016A
	beq L017F
L016C
	rol <$04
L016E
	fcb $02
L016F
	brn L0181
L0171
	bvc L01A7
L0173
	abx
L0174
	mul
L0175
	fcb $3E
L0176
	swi
L0177
	tfr Y,$F
L0179
	lbsr L0C81
L017C
	fcb $02
L017D
	fcb $01
L017E
	fcb $00
L017F
	neg <$20
L0181
	fcb $10,$28
L0183
	fcb $14
L0184
	dec <$05
L0186
	fcb $02
L0187
	fcb $01
L0188
	fcb $20
L0189
	fcb $10,$08
L018B
	bcc L019F
L018D
	rol <$24
L018F
	leas -7,X
L0191
	fcb $0C
L0192
	bne L01C7
L0194
	daa
L0195
	bge L01AD
L0197
	fcb $0B
L0198
	fcb $05
L0199
	fcb $02
L019A
	brn L01AC
L019C
	asl <$04
L019E
	fcb $02
L019F
	fcb $01
L01A0
	bra L01D2
L01A2
	fcb $18
L01A3
	inc <$06
L01A5
	com <$01
L01A7
	bra L01D9
L01A9
	fcb $18
L01AA
	bge L01E2
L01AC
	rti
L01AD
	mul
L01AE
	exg Y,$F
L01B0
	pulu CC,A,DP,X,Y
L01B2
	mul
L01B3
	fcb $3E
L01B4
	swi
L01B5
	swi
L01B6
	tfr Y,$F
L01B8
	lbsr L0CC0
L01BB
	bhi L01EE
L01BD
	fcb $18
L01BE
	bge L01D6
L01C0
	fcb $0B
L01C1
	bcs L01D5
L01C3
	rol <$04
L01C5
	fcb $02
L01C6
	brn L01D8
L01C8
	bvc L01FE
L01CA
	abx
L01CB
	sex
L01CC
	bgt L01E5
L01CE
	fcb $0B
L01CF
	bcs L01E3
L01D1
	fcb $09
L01D2
	lsr <$02
L01D4
	fcb $01
L01D5
	fcb $00
L01D6
	bra L0208
L01D8
	fcb $18
L01D9
	inc <$26
L01DB
	sync
L01DC
	rol <$24
L01DE
	nop
L01DF
	bvs L01F5
L01E1
	fcb $2A
L01E2
	fcb $35
L01E3
	abx
L01E4
	sex
L01E5
	jmp <$27
L01E7
	sync
L01E8
	rol <$04
L01EA
	bhi L021D
L01EC
	fcb $18
L01ED
	fcb $2C
L01EE
	lbra L2D06
L01F1
	bpl L0228
L01F3
	orcc #$2D
L01F5
	pshu CC,A,DP,X
L01F7
	blt L022F
L01F9
	rti
L01FA
	mul
L01FB
	exg D,$F
L01FD
	fcb $27
L01FE
	leau -7,X
L0200
	neg <$00
L0202
	neg <$01
L0204
	fcb $01
L0205
	fcb $01
L0206
	fcb $01
L0207
	fcb $02
L0208
	fcb $02
L0209
	fcb $02
L020A
	fcb $02
L020B
	com <$03
L020D
	com <$03
L020F
	lsr <$04
L0211
	lsr <$04
L0213
	fcb $05
L0214
	fcb $05
L0215
	fcb $05
L0216
	fcb $05
L0217
	fcb $06
L0218
	ror <$06
L021A
	ror <$07
L021C
	fcb $07
L021D
	asr <$07
L021F
	asl <$08
L0221
	asl <$08
L0223
	rol <$09
L0225
	rol <$09
L0227
	fcb $0A
L0228
	dec <$0A
L022A
	dec <$0B
L022C
	fcb $0B
L022D
	fcb $0B
L022E
	fcb $0B
L022F
	inc <$0C
L0231
	fcb $0C
L0232
	inc <$0D
L0234
	tst <$0D
L0236
	tst <$0E
L0238
	jmp <$0E
L023A
	jmp <$0F
L023C
	clr <$0F
L023E
	clr <$10
L0240
	fcb $10,$10
L0242
	fcb $10,$10
L0244
	fcb $11,$11
L0246
	fcb $11,$11
L0248
	nop
L0249
	nop
L024A
	nop
L024B
	nop
L024C
	sync
L024D
	sync
L024E
	sync
L024F
	sync
L0250
	fcb $14
L0251
	fcb $14
L0252
	fcb $14
L0253
	fcb $14
L0254
	fcb $15
L0255
	fcb $15
L0256
	fcb $15
L0257
	fcb $15
L0258
	lbra L1871
L025B
	lbra L1975
L025E
	lbsr L1979
L0261
	fcb $18
L0262
	fcb $18
L0263
	fcb $18
L0264
	daa
L0265
	daa
L0266
	daa
L0267
	daa
L0268
	orcc #$1A
L026A
	orcc #$1A
L026C
	fcb $1B
L026D
	fcb $1B
L026E
	fcb $1B
L026F
	fcb $1B
L0270
	andcc #$1C
L0272
	andcc #$1C
L0274
	sex
L0275
	sex
L0276
	sex
L0277
	sex
L0278
	exg X,$E
L027A
	exg X,$E
L027C
	tfr X,$F
L027E
	tfr X,$F
L0280
	bra L02A2
L0282
	bra L02A4
L0284
	bra L02A7
L0286
	brn L02A9
L0288
	brn L02AC
L028A
	bhi L02AE
L028C
	bhi L02B1
L028E
	bls L02B3
L0290
	bls L02B6
L0292
	bcc L02B8
L0294
	bcc L02BB
L0296
	bcs L02BD
L0298
	bcs L02C0
L029A
	bne L02C2
L029C
	bne L02C5
L029E
	beq L02C7
L02A0
	beq L02CA
L02A2
	bvc L02CC
L02A4
	bvc L02CF
L02A6
	fcb $29
L02A7
	bvs L02D2
L02A9
	bpl L02D5
L02AB
	fcb $2A
L02AC
	bpl L02D9
L02AE
	bmi L02DB
L02B0
	fcb $2B
L02B1
	bge L02DF
L02B3
	bge L02E1
L02B5
	fcb $2D
L02B6
	blt L02E5
L02B8
	blt L02E8
L02BA
	fcb $2E
L02BB
	bgt L02EB
L02BD
	ble L02EE
L02BF
	fcb $2F
L02C0
	ble L02F1
L02C2
	leax -16,Y
L02C4
	fcb $30
L02C5
	leax -15,Y
L02C7
	leay -15,Y
L02C9
	fcb $31
L02CA
	leas -14,Y
L02CC
	leas -14,Y
L02CE
	fcb $33
L02CF
	leau -13,Y
L02D1
	leau -12,Y
L02D3
	fcb $34
L02D4
	pshs B,X,Y
L02D6
	puls CC,B,X,Y
L02D8
	fcb $35
L02D9
	puls A,B,X,Y
L02DB
	pshu A,B,X,Y
L02DD
	fcb $36
L02DE
	pulu CC,A,B,X,Y
L02E0
	pulu CC,A,B,X,Y
L02E2
	fcb $38
L02E3
	fcb $38
L02E4
	fcb $38
L02E5
	fcb $38
L02E6
	rts
L02E7
	rts
L02E8
	rts
L02E9
	rts
L02EA
	abx
L02EB
	abx
L02EC
	abx
L02ED
	abx
L02EE
	rti
L02EF
	rti
L02F0
	rti
L02F1
	rti
L02F2
	cwai #$3C
L02F4
	cwai #$3C
L02F6
	mul
L02F7
	mul
L02F8
	mul
L02F9
	mul
L02FA
	fcb $3E
L02FB
	fcb $3E
L02FC
	fcb $3E
L02FD
	fcb $3E
L02FE
	swi
L02FF
	swi
	end
