***********************************************************************
* CoCoIDE SFX player — auto-generated (re-export from SFX Lab)
*
* API:
*   SoundInit  — enable DAC mux safely (call once)
*   PlaySfx    — A = effect id 0..3-1 (blocks until done)
*
* Clobbers: A,B,X,Y,U,CC
* Hardware: 6-bit DAC $FF20; mux ORA #$08 only (never full-byte PIA smash)
* Tables: sfx_tables.bin (768 bytes = 3 x 256)
* Wavetable model inspired by Paul Fiscarelli CoCoWG (samples 0-63).
***********************************************************************

SFXCOUNT        equ     3

                org     $3F00

START
                lbsr    SoundInit
* Demo: play all effects once (so audio is obvious), then key loop.
* 1/2/3… = SFX 0/1/2… ; Q = return to BASIC.
* Auto-play avoids hanging if POLCAT is awkward right after EXEC.
                clra
DemoAuto
                pshs    a
                lbsr    PlaySfx
                * short gap between effects
                ldx     #$4000
da_w            leax    -1,x
                bne     da_w
                puls    a
                inca
                cmpa    #SFXCOUNT
                blo     DemoAuto

* After auto-play, return to BASIC (reliable). Interactive keys optional:
* hold a key during the gap if your emulator needs it — primary path is auto.
DemoDone
                rts

POLCAT          equ     $A000

* Optional interactive wait (not used by default START path).
* Returns A=key, or A=0 on timeout so caller never hangs forever.
WaitKey
                pshs    b,x
                andcc   #$EF
                lbsr    KeyFlush
                ldy     #$0003          ; outer timeout ~ few seconds
wk_o            ldx     #$8000
wk_wt           jsr     [POLCAT]
                anda    #$7F
                bne     wk_hit
                leax    -1,x
                bne     wk_wt
                leay    -1,y
                bne     wk_o
                clra                    ; timeout
                puls    b,x
                rts
wk_hit          sta     ,-s
                ldx     #$4000
wk_up           jsr     [POLCAT]
                anda    #$7F
                beq     wk_got
                leax    -1,x
                bne     wk_up
wk_got          lda     ,s+
                puls    b,x
                rts

KeyFlush
                pshs    a,x
                ldx     #$1800
kf1             jsr     [POLCAT]
                anda    #$7F
                beq     kf2
                leax    -1,x
                bne     kf1
kf2             puls    a,x
                rts


***********************************************************************
SoundInit
                pshs    a
                orcc    #$50
                * Mux enable only (bit 3). Do not STA #$3C on keyboard PIA.
                lda     $FF01
                ora     #$08
                sta     $FF01
                lda     $FF03
                ora     #$08
                sta     $FF03
                lda     $FF23
                ora     #$08
                sta     $FF23
                * Point $FF20 at DDR, set PA7-2 as outputs, restore data reg
                * Write $FC only while DDR selected (not as a DAC sample).
                lda     $FF21
                anda    #$FB
                sta     $FF21
                lda     #$FC
                sta     $FF20
                lda     $FF21
                ora     #$04
                sta     $FF21
                * quiet mid-level (one settle, not a full-scale blip)
                lda     #$80
                sta     $FF20
                andcc   #$AF            ; IRQs on again (keyboard ROM needs them)
                puls    a
                rts

***********************************************************************
* PlaySfx — A = effect id
*
* Each "tick" outputs one wavetable sample then delays. Delay scales with
* pitch (higher pitch → shorter delay → higher tone). Length is in ticks.
* Old v1 used delay~10 cycles (tones were ~2ms clicks). Now delay is
* hundreds of cycles so effects are clearly audible.
PlaySfx
                pshs    cc,a,b,x,y,u
                orcc    #$50
                cmpa    #SFXCOUNT
                lbhs    ps_done
                ldb     #8
                mul
                ldu     #SfxCat
                leau    d,u
                lda     1,u
                sta     SfxFlags
                lda     2,u
                sta     SfxPitch
                lda     3,u
                sta     SfxPend
                lda     4,u
                ldb     5,u
                std     SfxLen
                lda     6,u
                sta     SfxVol
                lda     ,u
                clrb
                tfr     d,x
                leax    SfxTables,x
                stx     SfxTab
                clr     SfxPhase
                lda     $FF23
                ora     #$08
                sta     $FF23
                * PB1 out enable (helps XRoar / some hardware hear tone)
                lda     $FF23
                anda    #$FB
                sta     $FF23
                lda     $FF22
                ora     #$02
                sta     $FF22
                lda     $FF23
                ora     #$04
                sta     $FF23
                ldd     SfxLen
                lbeq    ps_quiet

ps_loop
                lda     SfxFlags
                bita    #$01
                bne     ps_noise
                ldx     SfxTab
                lda     SfxPhase
                lda     a,x
                bra     ps_scale
ps_noise
                ldd     SfxLfsr
                bne     ps_n1
                ldd     #$ACE1
ps_n1           eora    SfxLfsr+1
                lsra
                rorb
                eora    SfxLfsr
                std     SfxLfsr
                lda     SfxLfsr+1
                anda    #63
ps_scale
                * A=0..63 → DAC bits; also drive PB1 from sample MSB
                ldb     SfxVol
                mul
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                tfr     b,a
                lsla
                lsla
                anda    #$FC
                sta     $FF20
                * PB1: bit1 of $FF22 follow sample energy
                tfr     a,b
                lda     $FF22
                andb    #$80
                beq     ps_p0
                ora     #$02
                bra     ps_p1
ps_p0           anda    #$FD
ps_p1           sta     $FF22
                * advance table index by 1 (walk wave); pitch controls delay
                inc     SfxPhase
                * delay: base + (256-pitch)*scale  → higher pitch, less delay
                lda     #255
                suba    SfxPitch
                lsra                    ; 0..127
                inca
                tfr     a,b
                clra
                tfr     d,x             ; X = 1..128
                leax    40,x            ; minimum pad
ps_d1           ldb     #8
ps_d2           decb
                bne     ps_d2
                leax    -1,x
                bne     ps_d1
                * pitch slide
                lda     SfxPitch
                cmpa    SfxPend
                beq     ps_len
                blo     ps_inc
                dec     SfxPitch
                bra     ps_len
ps_inc          inc     SfxPitch
ps_len
                ldd     SfxLen
                subd    #1
                std     SfxLen
                lbne    ps_loop

ps_quiet
                lda     #$80
                sta     $FF20
ps_done
                andcc   #$AF
                puls    cc,a,b,x,y,u
                rts

***********************************************************************
* Catalog: wave_id, flags, pitch, pitch_end, len_hi, len_lo, vol, pad
SfxCat
        fcb     0,$00,$B4,$B4,$03,$20,$38,$00  * 0: blip
        fcb     1,$01,$78,$28,$04,$B0,$34,$00  * 1: splash
        fcb     2,$00,$C8,$1E,$05,$DC,$32,$00  * 2: dive

SfxTables
                includebin sfx_tables.bin

SfxFlags        rmb     1
SfxPitch        rmb     1
SfxPend         rmb     1
SfxVol          rmb     1
SfxLen          rmb     2
SfxPhase        rmb     2
SfxTab          rmb     2
SfxLfsr         fdb     $ACE1

                end     START
