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
PlaySfx
                pshs    cc,a,b,x,y,u
                orcc    #$50
                cmpa    #SFXCOUNT
                lbhs    ps_done
                * U = &SfxCat[A]
                ldb     #8
                mul                     ; D = A*8
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
                * X = SfxTables + id*256
                lda     ,u
                clrb
                tfr     d,x             ; D = id*256
                leax    SfxTables,x
                stx     SfxTab
                clr     SfxPhase
                clr     SfxPhase+1
                lda     $FF23
                ora     #$08
                sta     $FF23
                ldd     SfxLen
                lbeq    ps_quiet

ps_loop
                lda     SfxFlags
                bita    #$01
                bne     ps_noise
                * A = table[phase_hi]
                ldx     SfxTab
                lda     SfxPhase        ; high byte of phase
                lda     a,x
                bra     ps_scale
ps_noise
                * 16-bit LFSR step → A = 0..63
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
                * A = raw 0..63; level ~= (raw * vol) >> 6; DAC = level << 2
                ldb     SfxVol
                mul                     ; D = raw * vol
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
                rorb                    ; D >>= 6 → B
                tfr     b,a
                lsla
                lsla
                anda    #$FC
                sta     $FF20
                * phase_hi += pitch (8-bit step through 256-sample table)
                lda     SfxPhase
                adda    SfxPitch
                sta     SfxPhase
                * slide pitch toward pitch_end
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
                lbeq    ps_quiet
                ldb     #10
ps_dly          decb
                bne     ps_dly
                bra     ps_loop

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
        fcb     0,$00,$30,$30,$00,$64,$32,$00  * 0: blip
        fcb     1,$00,$46,$08,$02,$26,$2A,$00  * 1: dive
        fcb     2,$01,$1C,$06,$01,$7C,$30,$00  * 2: splash

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
