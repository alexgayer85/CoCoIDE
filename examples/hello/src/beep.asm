***********************************************************************
* CoCoIDE sample — short DAC tone (CoCo 1/2/3)
* Build → BEEP.BIN on disk. From BASIC:
*   AUDIO ON
*   LOADM"BEEP":EXEC
*
* CoCo sound is the 6-bit DAC at $FF20. AUDIO ON / PIA setup enables the path.
***********************************************************************

		org	$3F00

START
		; --- enable 6-bit sound path (PIA) ---
		lda	$FF01
		ora	#$08		; CA2 / sound-related enable
		sta	$FF01
		lda	#$3C
		sta	$FF03		; CB2 output high (common enable pattern)
		lda	#$3C
		sta	$FF23

		ldb	#30		; outer loops (length)
outer
		lda	#$80
inner
		sta	$FF20		; DAC
		eora	#$3F		; toggle upper DAC bits → tone
		sta	$FF20
		ldx	#40
delay
		leax	-1,x
		bne	delay
		deca
		bne	inner
		decb
		bne	outer
		rts

		end	START
