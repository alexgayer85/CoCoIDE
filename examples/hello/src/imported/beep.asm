****************************************
* CoCoIDE 6809 disassembly (best-effort)
* Review before re-assembling with lwasm
****************************************

		org	$3F00
* segment load=$3F00 len=44
L3F00	LDA	$FF01
L3F03	ORA	#$08
L3F05	STA	$FF01
L3F08	LDA	#$3C
L3F0A	STA	$FF03
L3F0D	LDA	#$3C
L3F0F	STA	$FF23
L3F12	LDB	#$1E
L3F14	LDA	#$80
L3F16	STA	$FF20
L3F19	EORA	#$3F
L3F1B	STA	$FF20
L3F1E	LDX	#$0028
L3F21	LEAX	-1,X
L3F23	BNE	L3F21
L3F25	DECA
L3F26	BNE	L3F16
L3F28	DECB
L3F29	BNE	L3F14
L3F2B	RTS

		end	$3F00
