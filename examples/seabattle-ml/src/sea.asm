***********************************************************************
* Sea Battle ML — CoCo 1/2/3 · PMODE 4 dual boards · matrix keyboard
*
* Loader (main.bas):
*   CLEAR200,&H3F00 : PCLEAR4 : PMODE4,1 : PCLS : SCREEN1,1
*   LOADM"SEA" : EXEC
*
* Controls (no typed coords — reliable under XRoar):
*   WASD / arrows  move cursor
*   Space / Enter  fire or place
*   R              rotate ship (placement)
*   A              auto-place remaining fleet
*   F              (battle) flash own fleet highlight only — boards stay dual
***********************************************************************

* Hardware
PIA0    equ     $FF00           ; keyboard rows (R)
PIA0D   equ     $FF02           ; keyboard columns (W)
DAC     equ     $FF20
PIA1CRA equ     $FF01
PIA1CRB equ     $FF03
PIA2CRB equ     $FF23

* PMODE 4 page 1 (after PCLEAR 4 / PMODE 4,1)
GFX     equ     $0E00
GROWS   equ     192
GBPL    equ     32              ; bytes per line

* Board geometry — CELL=8 so each cell row is exactly one PM4 byte (fast)
CELL    equ     8
* Left fleet board (X must stay multiple of 8)
LX0     equ     16
LY0     equ     24
* Right radar board
RX0     equ     144
RY0     equ     24

        org     $3F00

***********************************************************************
START
        clra
        tfr     a,dp
        lbsr    SoundInit
        lbsr    SeedRnd
        lbsr    InitGame
        lbsr    TitleScreen
        lbsr    PlacePlayerFleet
        lbsr    PlaceEnemyFleet
        lbsr    BattleLoop
        lbsr    GameOver
        rts

***********************************************************************
* Init grids / ships
***********************************************************************
InitGame
        ldx     #PS
        lbsr    Clear100
        ldx     #ES
        lbsr    Clear100
        ldx     #RD
        lbsr    Clear100
        ldx     #AK
        lbsr    Clear100
        * ship lengths / remaining (explicit stores)
        ldx     #SL
        lda     #5
        sta     ,x+
        lda     #4
        sta     ,x+
        lda     #3
        sta     ,x+
        sta     ,x+
        lda     #2
        sta     ,x+
        ldx     #SR
        lda     #5
        sta     ,x+
        lda     #4
        sta     ,x+
        lda     #3
        sta     ,x+
        sta     ,x+
        lda     #2
        sta     ,x+
        lda     #17
        sta     PH
        sta     EH
        clr     Hunt
        clr     HR
        clr     HC
        lda     #1
        sta     CurR
        sta     CurC
        clr     Horiz
        rts

Clear100
        ldb     #100
c1      clr     ,x+
        decb
        bne     c1
        rts

***********************************************************************
* Title (bitmap)
***********************************************************************
TitleScreen
        lbsr    GfxCls
        leax    TTitle,pcr
        lda     #40             ; X multiple of 8 for fast blit
        ldb     #40
        lbsr    DrawStr
        leax    TSub,pcr
        lda     #32
        ldb     #60
        lbsr    DrawStr
        leax    TCtrl,pcr
        lda     #8
        ldb     #100
        lbsr    DrawStr
        leax    TCtrl2,pcr
        lda     #8
        ldb     #112
        lbsr    DrawStr
        leax    TGo,pcr
        lda     #40
        ldb     #152
        lbsr    DrawStr
        lbsr    WaitKey
        rts

***********************************************************************
* Placement
***********************************************************************
PlacePlayerFleet
        lda     #1
        sta     ShipId
        clr     Horiz           ; 0=vert 1=horiz
pp_loop
        lda     ShipId
        cmpa    #6
        lbhs    pp_done
pp_draw
        lbsr    DrawBoardsOnly  ; no battle labels (avoids overlap)
        lbsr    DrawPlaceHUD
        lbsr    DrawScores
        lbsr    DrawCursorLeft
pp_in
        lbsr    WaitKey
        tsta
        lbeq    pp_in
        * WASD movement (A = left, NOT auto)
        cmpa    #'D
        lbeq    pp_r
        cmpa    #'d
        lbeq    pp_r
        cmpa    #'A
        lbeq    pp_l
        cmpa    #'a
        lbeq    pp_l
        cmpa    #'S
        lbeq    pp_dn
        cmpa    #'s
        lbeq    pp_dn
        cmpa    #'W
        lbeq    pp_u
        cmpa    #'w
        lbeq    pp_u
        * extras
        cmpa    #'L
        lbeq    pp_r
        cmpa    #'l
        lbeq    pp_r
        cmpa    #'J
        lbeq    pp_l
        cmpa    #'j
        lbeq    pp_l
        cmpa    #'I
        lbeq    pp_u
        cmpa    #'i
        lbeq    pp_u
        cmpa    #'K
        lbeq    pp_dn
        cmpa    #'k
        lbeq    pp_dn
        cmpa    #9              ; right arrow
        lbeq    pp_r
        cmpa    #8              ; left arrow / BS
        lbeq    pp_l
        cmpa    #10             ; down arrow
        lbeq    pp_dn
        cmpa    #94             ; up arrow (common CoCo / XRoar)
        lbeq    pp_u
        cmpa    #12             ; up alt
        lbeq    pp_u
        cmpa    #11             ; up alt
        lbeq    pp_u
        cmpa    #30             ; up alt
        lbeq    pp_u
        cmpa    #28             ; up alt
        lbeq    pp_u
        cmpa    #'^
        lbeq    pp_u
        cmpa    #'R
        lbeq    pp_rot
        cmpa    #'r
        lbeq    pp_rot
        cmpa    #'P
        lbeq    pp_auto
        cmpa    #'p
        lbeq    pp_auto
        cmpa    #'0
        lbeq    pp_auto
        cmpa    #'1
        lbeq    pp_auto
        cmpa    #'U
        lbeq    pp_auto
        cmpa    #'u
        lbeq    pp_auto
        cmpa    #32
        lbeq    pp_put
        cmpa    #13
        lbeq    pp_put
        lbra    pp_in
pp_rot
        lda     Horiz
        eora    #1
        sta     Horiz
        lbra    pp_draw
pp_r    lda     CurC
        cmpa    #10
        lbhs    pp_in
        lbsr    UndrawCursorLeft
        inc     CurC
        lbsr    ClampCur
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_l    lda     CurC
        cmpa    #1
        lbls    pp_in
        lbsr    UndrawCursorLeft
        dec     CurC
        lbsr    ClampCur
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_dn   lda     CurR
        cmpa    #10
        lbhs    pp_in
        lbsr    UndrawCursorLeft
        inc     CurR
        lbsr    ClampCur
        lbsr    DrawCursorLeft
        lbra    pp_in
pp_u    lda     CurR
        cmpa    #1
        lbls    pp_in
        lbsr    UndrawCursorLeft
        dec     CurR
        lbsr    ClampCur
        lbsr    DrawCursorLeft
        lbra    pp_in

ClampCur
        lda     CurR
        bne     cc1
        lda     #1
cc1     cmpa    #10
        bls     cc2
        lda     #10
cc2     sta     CurR
        lda     CurC
        bne     cc3
        lda     #1
cc3     cmpa    #10
        bls     cc4
        lda     #10
cc4     sta     CurC
        rts
pp_put
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        clr     TmpG
        lbsr    ShipLen         ; → B = SL(ShipId)
        stb     TmpL
        lbsr    CanPlace
        lda     CP
        lbeq    pp_bad
        lda     #0
        ldb     ShipId
        lbsr    PlaceShip
        inc     ShipId
        lda     #1
        lbsr    Beep
        lbra    pp_loop
pp_bad
        lda     #0
        lbsr    Beep
        lbra    pp_in
pp_auto
        * Click DAC first (no Beep routine — proves we reached here)
        lda     #$20
        sta     DAC
        eora    #$3F
        sta     DAC
        lbsr    AutoPlacePlayer
        lda     #6
        sta     ShipId
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lbsr    DrawOneBoard
        lda     #$20
        sta     DAC
        rts

pp_done
        lbsr    DrawBoardsOnly
        lda     #1
        lbsr    Beep
        rts

DrawPlaceHUD
        * top banner only (y=2..16) — not over boards at y=24
        leax    TPlace,pcr
        lda     #8
        ldb     #2
        lbsr    DrawStr
        leax    THint,pcr
        lda     #8
        ldb     #12
        lbsr    DrawStr
        rts

PlaceEnemyFleet
        lbsr    GfxCls
        leax    TComp,pcr
        lda     #40
        ldb     #90
        lbsr    DrawStr
        lda     #1
        lbsr    AutoPlaceFleet
        rts

***********************************************************************
* Auto-place player fleet: raw stores into PS[10][10] row-major.
* Rows 0..4, each ship starting at column 0. Cannot hang.
***********************************************************************
AutoPlacePlayer
        ldx     #PS
        ldb     #100
app_cl  clr     ,x+
        decb
        bne     app_cl
        * row 0: ship 1 length 5
        ldx     #PS
        lda     #1
        sta     ,x+
        sta     ,x+
        sta     ,x+
        sta     ,x+
        sta     ,x+
        * row 1: ship 2 length 4  (PS+10)
        ldx     #PS
        leax    10,x
        lda     #2
        sta     ,x+
        sta     ,x+
        sta     ,x+
        sta     ,x+
        * row 2: ship 3 length 3
        ldx     #PS
        leax    20,x
        lda     #3
        sta     ,x+
        sta     ,x+
        sta     ,x+
        * row 3: ship 4 length 3
        ldx     #PS
        leax    30,x
        lda     #4
        sta     ,x+
        sta     ,x+
        sta     ,x+
        * row 4: ship 5 length 2
        ldx     #PS
        leax    40,x
        lda     #5
        sta     ,x+
        sta     ,x+
        rts

***********************************************************************
* Auto-place enemy fleet into ES (mirror of player layout)
***********************************************************************
AutoPlaceFleet
        * A=grid ignored for enemy path when called with 1 from PlaceEnemy
        * Always fill ES the same way
        ldx     #ES
        ldb     #100
ape_cl  clr     ,x+
        decb
        bne     ape_cl
        ldx     #ES
        lda     #1
        sta     ,x+
        sta     ,x+
        sta     ,x+
        sta     ,x+
        sta     ,x+
        ldx     #ES
        leax    10,x
        lda     #2
        sta     ,x+
        sta     ,x+
        sta     ,x+
        sta     ,x+
        ldx     #ES
        leax    20,x
        lda     #3
        sta     ,x+
        sta     ,x+
        sta     ,x+
        ldx     #ES
        leax    30,x
        lda     #4
        sta     ,x+
        sta     ,x+
        sta     ,x+
        ldx     #ES
        leax    40,x
        lda     #5
        sta     ,x+
        sta     ,x+
        rts

* ShipId (1..5) → B = length
ShipLen
        pshs    a,x
        lda     ShipId
        beq     sl0
        cmpa    #5
        bls     sl1
        lda     #5
sl1     deca
        leax    LenTab,pcr
        lda     a,x
        tfr     a,b
        puls    a,x
        rts
sl0     ldb     #2
        puls    a,x
        rts

LenTab  fcb     5,4,3,3,2

***********************************************************************
* CanPlace / PlaceShip / CellAddr
***********************************************************************
CanPlace
        lda     #1
        sta     CP
        clr     TmpI
cpl     lda     TmpI
        cmpa    TmpL
        bhs     cpo
        lda     TmpR
        ldb     TmpC
        tst     Horiz
        beq     cpv
        addb    TmpI
        bra     cpb
cpv     adda    TmpI
cpb     tsta
        beq     cpf
        cmpa    #10
        bhi     cpf
        tstb
        beq     cpf
        cmpb    #10
        bhi     cpf
        sta     RR
        stb     CC
        lda     TmpG
        bne     cpe
        ldx     #PS
        bra     cpx
cpe     ldx     #ES
cpx     lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        bne     cpf
        inc     TmpI
        bra     cpl
cpf     clr     CP
cpo     rts

PlaceShip
        sta     TmpG
        stb     ShipId
        lbsr    ShipLen
        stb     TmpL
PlaceShipRaw
        * uses TmpG, ShipId, TmpR, TmpC, Horiz, TmpL
        clr     TmpI
psl     lda     TmpI
        cmpa    TmpL
        bhs     psx
        lda     TmpR
        ldb     TmpC
        tst     Horiz
        beq     psv
        addb    TmpI
        bra     psb
psv     adda    TmpI
psb     sta     RR
        stb     CC
        lda     TmpG
        bne     pse
        ldx     #PS
        bra     psw
pse     ldx     #ES
psw     lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ShipId
        sta     ,x
        inc     TmpI
        bra     psl
psx     rts

* X=base A=row1-10 B=col1-10 → X=&cell
CellAddr
        deca
        decb
        pshs    b
        ldb     #10
        mul
        addb    ,s+
        abx
        rts

***********************************************************************
* Battle
***********************************************************************
BattleLoop
bl      lda     EH
        lbeq    bld
        lda     PH
        lbeq    bld
        lbsr    PlayerTurn
        lda     EH
        lbeq    bld
        lbsr    ComputerTurn
        lda     PH
        lbeq    bld
        lbra    bl
bld     rts

PlayerTurn
pt_d    lbsr    DrawBattle      ; boards + battle HUD + scores
        lbsr    DrawCursorRight
pt_i    lbsr    WaitKey
        tsta
        lbeq    pt_i
        cmpa    #'F
        lbeq    pt_d
        cmpa    #'f
        lbeq    pt_d
        cmpa    #'D
        lbeq    pt_r
        cmpa    #'d
        lbeq    pt_r
        cmpa    #'L
        lbeq    pt_r
        cmpa    #'l
        lbeq    pt_r
        cmpa    #9
        lbeq    pt_r
        cmpa    #'A
        lbeq    pt_l
        cmpa    #'a
        lbeq    pt_l
        cmpa    #'J
        lbeq    pt_l
        cmpa    #'j
        lbeq    pt_l
        cmpa    #8
        lbeq    pt_l
        cmpa    #'S
        lbeq    pt_dn
        cmpa    #'s
        lbeq    pt_dn
        cmpa    #10
        lbeq    pt_dn
        cmpa    #'W
        lbeq    pt_up
        cmpa    #'w
        lbeq    pt_up
        cmpa    #'I
        lbeq    pt_up
        cmpa    #'i
        lbeq    pt_up
        cmpa    #'K
        lbeq    pt_dn
        cmpa    #'k
        lbeq    pt_dn
        cmpa    #94
        lbeq    pt_up
        cmpa    #12
        lbeq    pt_up
        cmpa    #11
        lbeq    pt_up
        cmpa    #30
        lbeq    pt_up
        cmpa    #28
        lbeq    pt_up
        cmpa    #'^
        lbeq    pt_up
        cmpa    #32
        lbeq    pt_fire
        cmpa    #13
        lbeq    pt_fire
        lbra    pt_i
pt_r    lda     CurC
        cmpa    #10
        lbhs    pt_i
        lbsr    UndrawCursorRight
        inc     CurC
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_l    lda     CurC
        cmpa    #1
        lbls    pt_i
        lbsr    UndrawCursorRight
        dec     CurC
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_dn   lda     CurR
        cmpa    #10
        lbhs    pt_i
        lbsr    UndrawCursorRight
        inc     CurR
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_up   lda     CurR
        cmpa    #1
        lbls    pt_i
        lbsr    UndrawCursorRight
        dec     CurR
        lbsr    ClampCur
        lbsr    DrawCursorRight
        lbra    pt_i
pt_fire
        lda     CurR
        sta     TmpR
        lda     CurC
        sta     TmpC
        lda     #1
        lbsr    ApplyShot
        * refresh only the shot cell on radar (fast)
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbsr    DrawOneCell
        lbsr    DrawCursorRight
        lbsr    DrawScores
        lda     HT
        cmpa    #2
        lbeq    pt_al
        cmpa    #0
        lbeq    pt_ms
        cmpa    #3
        lbeq    pt_sk
        leax    TMHit,pcr
        lbra    pt_msg
pt_ms   leax    TMMiss,pcr
        lbra    pt_msg
pt_sk   leax    TMSunk,pcr
        lbra    pt_msg
pt_al   leax    TMAlr,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        lbsr    TinyPause
        lbra    pt_i
pt_msg
        * X already → message string (HIT!/MISS!/SUNK!)
        pshs    x
        lbsr    ClearMsg
        puls    x
        lda     #8
        ldb     #180
        lbsr    DrawStr
        lbsr    TinyPause
        * Do NOT WaitKey / Beep here — return so BattleLoop runs ComputerTurn
        rts

ComputerTurn
        lbsr    ClearMsg
        leax    TMComp,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        lbsr    TinyPause
        lbsr    AiPick
        * clamp AI coords
        lda     AR
        beq     ct_fix
        cmpa    #10
        bls     ct_ar
ct_fix lda     #1
        sta     AR
ct_ar   lda     AC
        beq     ct_fc
        cmpa    #10
        bls     ct_ac
ct_fc   lda     #1
        sta     AC
ct_ac
        lda     AR
        sta     TmpR
        lda     AC
        sta     TmpC
        clra
        lbsr    ApplyShot
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lda     AR
        sta     RR
        lda     AC
        sta     CC
        lbsr    DrawOneCell
        lbsr    DrawScores
        leax    TMComp2,pcr
        lda     #8
        ldb     #180
        lbsr    DrawStr
        lda     HT
        cmpa    #1
        blo     ct_m
        cmpa    #3
        beq     ct_s
        lda     #1
        sta     Hunt
        lda     AR
        sta     HR
        lda     AC
        sta     HC
        bra     ct_end
ct_m    bra     ct_end
ct_s    clr     Hunt
ct_end  lbsr    TinyPause
        lbsr    ClearMsg
        rts

ClearMsg
        pshs    a,b,x
        lda     #180
        ldb     #GBPL
        mul
        tfr     d,x
        leax    GFX,x
        ldb     #32
        clra
cm1     sta     ,x+
        decb
        bne     cm1
        puls    a,b,x
        rts

* ~brief delay; register counter only
TinyPause
        pshs    x
        ldx     #$1000
tp1     leax    -1,x
        bne     tp1
        puls    x
        rts
PauseShort
        bra     TinyPause
PauseMed
        bra     TinyPause

DrawBattleHUD
        leax    TYou,pcr
        lda     #LX0
        ldb     #8
        lbsr    DrawStr
        leax    TRad,pcr
        lda     #RX0
        ldb     #8
        lbsr    DrawStr
        leax    TStat,pcr
        lda     #8
        ldb     #168
        lbsr    DrawStr
        rts

***********************************************************************
* ApplyShot A=grid(0 player /1 enemy) TmpR,TmpC → HT
***********************************************************************
ApplyShot
        sta     TmpG
        clr     HT
        clr     SID
        lda     TmpG
        lbne    ase
        ldx     #PS
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        cmpa    #6
        lbeq    asal
        cmpa    #7
        lbeq    asal
        tsta
        lbeq    aspm
        cmpa    #5
        lbhi    asx
        sta     SID
        lda     #7
        sta     ,x
        ldx     #AK
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #2
        sta     ,x
        dec     PH
        lda     #1
        sta     HT
        lbsr    CountShipPS
        lda     TmpCnt
        lbne    asx
        lda     #3
        sta     HT
        lbra    asx
aspm    lda     #6
        sta     ,x
        ldx     #AK
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #1
        sta     ,x
        clr     HT
        lbra    asx
ase     ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        lbne    asal
        ldx     #ES
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        tsta
        lbeq    asem
        cmpa    #5
        lbhi    asx
        sta     SID
        lda     #7
        sta     ,x
        ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #2
        sta     ,x
        * dec SR[SID-1]
        ldx     #SR
        lda     SID
        deca
        leax    a,x
        dec     ,x
        dec     EH
        lda     #1
        sta     HT
        lda     ,x
        lbne    asx
        lda     #3
        sta     HT
        lbra    asx
asem    ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #1
        sta     ,x
        clr     HT
        lbra    asx
asal    lda     #2
        sta     HT
asx     rts

CountShipPS
        clr     TmpCnt
        lda     #1
        sta     RR
csr     lda     #1
        sta     CC
csc     ldx     #PS
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        cmpa    SID
        bne     csn
        inc     TmpCnt
csn     inc     CC
        lda     CC
        cmpa    #11
        blo     csc
        inc     RR
        lda     RR
        cmpa    #11
        blo     csr
        rts

***********************************************************************
* AI — linear scan only (no random; cannot hang)
***********************************************************************
AiPick
        * Prefer neighbors if hunting
        lda     Hunt
        beq     ai_scan
        lda     HR
        beq     ai_scan
        * try N S W E
        lda     HR
        deca
        ldb     HC
        lbsr    ai_try
        bcc     ai_got
        lda     HR
        inca
        ldb     HC
        lbsr    ai_try
        bcc     ai_got
        lda     HR
        ldb     HC
        decb
        lbsr    ai_try
        bcc     ai_got
        lda     HR
        ldb     HC
        incb
        lbsr    ai_try
        bcc     ai_got
        clr     Hunt
ai_scan lda     #1
        sta     AR
ais_r   lda     #1
        sta     AC
ais_c   ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        beq     ai_got          ; empty → take it (AR/AC already set)
        inc     AC
        lda     AC
        cmpa    #11
        blo     ais_c
        inc     AR
        lda     AR
        cmpa    #11
        blo     ais_r
        lda     #1
        sta     AR
        sta     AC
ai_got  rts

* A=row B=col → if valid empty on AK, set AR/AC and clear carry; else set carry
ai_try
        tsta
        beq     ait_bad
        cmpa    #10
        bhi     ait_bad
        tstb
        beq     ait_bad
        cmpb    #10
        bhi     ait_bad
        sta     RR
        stb     CC
        ldx     #AK
        lbsr    CellAddr
        lda     ,x
        bne     ait_bad
        lda     RR
        sta     AR
        lda     CC
        sta     AC
        andcc   #$FE            ; clear C = success
        rts
ait_bad orcc    #$01            ; set C = fail
        rts

***********************************************************************
* Game over
***********************************************************************
GameOver
        lbsr    DrawBattle
        lda     EH
        bne     gol
        leax    TWin,pcr
        bra     gow
gol     leax    TLose,pcr
gow     lda     #80
        ldb     #100
        lbsr    DrawStr
        lbsr    WaitKey
        rts

***********************************************************************
* Draw PMODE 4 dual boards — ALL cell graphics are byte stores (fast).
* Empty cell = hollow box so the 10x10 grid is always visible.
* Cursor = XOR invert of cell (toggle twice = restore).
***********************************************************************
DrawBoardsOnly
        lbsr    GfxCls
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lbsr    DrawOneBoard
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lbsr    DrawOneBoard
        rts

DrawBattle
        lbsr    DrawBoardsOnly
        lbsr    DrawBattleHUD
        lbsr    DrawScores
        rts

DrawScores
        leax    TScE,pcr
        lda     #8
        ldb     #168
        lbsr    DrawStr
        lda     EH
        lbsr    DrawNum
        leax    TScY,pcr
        lbsr    DrawStrCont
        lda     PH
        lbsr    DrawNum
        rts

DrawOneBoard
        lda     #1
        sta     RR
dob_r   lda     #1
        sta     CC
dob_c   lbsr    DrawOneCell
        inc     CC
        lda     CC
        cmpa    #11
        blo     dob_c
        inc     RR
        lda     RR
        cmpa    #11
        blo     dob_r
        rts

* BoardWhich, BX0, BY0, RR, CC
DrawOneCell
        pshs    a,b,x
        lbsr    CellGlyph
        sta     GType
        lbsr    CellOrigin      ; → X0,Y0 from RR,CC,BX0,BY0
        lbsr    DrawCell
        puls    a,b,x
        rts

* RR,CC,BX0,BY0 → X0,Y0 (preserves RR/CC)
CellOrigin
        pshs    a,b
        lda     CC
        deca
        ldb     #CELL
        mul
        addb    BX0
        stb     X0
        lda     RR
        deca
        ldb     #CELL
        mul
        addb    BY0
        stb     Y0
        puls    a,b
        rts

* CellVal = raw grid byte; GType = 0 empty 1 ship 2 miss 3 hit
CellGlyph
        lda     BoardWhich
        bne     cg_r
        ldx     #PS
        bra     cg_g
cg_r    ldx     #RD
cg_g    lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        sta     CellVal
        tsta
        beq     cg0
        lda     BoardWhich
        bne     cg_rad
        lda     CellVal
        cmpa    #6
        beq     cg2
        cmpa    #7
        beq     cg3
        lda     #1
        rts
cg_rad  lda     CellVal
        cmpa    #1
        beq     cg2
        lda     #3
        rts
cg0     clra
        rts
cg2     lda     #2
        rts
cg3     lda     #3
        rts

* DrawCell using 8-byte patterns (ships look like mini hulls, not solid bars)
DrawCell
        lda     GType
        beq     dc_pat_e
        cmpa    #2
        beq     dc_pat_m
        cmpa    #3
        beq     dc_pat_h
        * ship id 1..5 → pattern
        lda     CellVal
        beq     dc_s1
        cmpa    #5
        bls     dc_sok
        lda     #1
dc_sok  deca
        ldb     #8
        mul
        leax    PatShip,pcr
        leax    d,x
        bra     CellBlit
dc_s1   leax    PatShip,pcr
        bra     CellBlit
dc_pat_m
        leax    PatMiss,pcr
        bra     CellBlit
dc_pat_h
        leax    PatHit,pcr
        bra     CellBlit
dc_pat_e
        leax    PatEmpty,pcr
* X → 8 row bytes; blit to X0,Y0
CellBlit
        pshs    x
        lbsr    CellAddrByte
        tfr     x,y             ; Y = screen
        puls    x               ; X = pattern
        ldb     #8
cbl     lda     ,x+
        sta     ,y
        lda     #GBPL
        leay    a,y
        decb
        bne     cbl
        rts

* Solid fill for cursor (A = fill byte)
CellFillA
        sta     TmpB
        lbsr    CellAddrByte
        ldb     #8
        lda     TmpB
cfa1    sta     ,x
        pshs    a,b
        lda     #GBPL
        leax    a,x
        puls    a,b
        decb
        bne     cfa1
        rts

PatEmpty
        fcb     $FF,$81,$81,$81,$81,$81,$81,$FF
PatMiss
        fcb     $00,$00,$18,$3C,$3C,$18,$00,$00
PatHit
        fcb     $81,$42,$24,$18,$18,$24,$42,$81
PatShip
        fcb     $00,$3C,$7E,$FF,$FF,$7E,$3C,$18
        fcb     $00,$18,$3C,$7E,$FF,$7E,$3C,$18
        fcb     $00,$00,$3C,$7E,$7E,$3C,$00,$00
        fcb     $00,$18,$3C,$7E,$3C,$18,$00,$00
        fcb     $00,$00,$18,$3C,$3C,$18,$00,$00

* X0,Y0 → X = &GFX + Y*32 + X/8
CellAddrByte
        pshs    a,b
        lda     Y0
        ldb     #GBPL
        mul
        tfr     d,x
        lda     X0
        lsra
        lsra
        lsra
        leax    a,x
        leax    GFX,x
        puls    a,b
        rts

UndrawCursorLeft
        lda     #0
        sta     BoardWhich
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbra    DrawOneCell

UndrawCursorRight
        lda     #1
        sta     BoardWhich
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbra    DrawOneCell

DrawCursorLeft
        lda     #LX0
        sta     BX0
        lda     #LY0
        sta     BY0
        bra     DrawCur
DrawCursorRight
        lda     #RX0
        sta     BX0
        lda     #RY0
        sta     BY0
DrawCur
        * Solid cursor block (no XOR state). Undraw restores via DrawOneCell.
        lda     CurR
        sta     RR
        lda     CurC
        sta     CC
        lbsr    CellOrigin
        lda     #$FF
        lbra    CellFillA

***********************************************************************
* Low-level PMODE 4 graphics
***********************************************************************
GfxCls
        ldx     #GFX
        ldy     #6144/2
        clra
        clrb
gc1     std     ,x++
        leay    -1,y
        bne     gc1
        rts

* Plot2: set pixel A=X (0-255), B=Y (0-191)
* Preserves X (DrawChar walks font data in X across Plot2 calls).
Plot2
        cmpb    #192
        bhs     p2x
        pshs    a,b,x
        sta     PixX
        stb     PixY
        lda     PixY
        ldb     #GBPL
        mul                     ; D = Y*32
        tfr     d,x
        lda     PixX
        lsra
        lsra
        lsra                    ; X/8
        leax    a,x
        leax    GFX,x
        lda     PixX
        anda    #7
        sta     TmpI
        lda     #$80
p2sh    tst     TmpI
        beq     p2or
        lsra
        dec     TmpI
        bra     p2sh
p2or    tfr     a,b
        orb     ,x
        stb     ,x
        puls    a,b,x
p2x     rts

FillRect2
        lda     Ht
        beq     fr2x
        sta     TY
        lda     RY
        sta     PY
fr2y    lda     Wd
        beq     fr2x
        sta     TX
        lda     RX
        sta     PX
fr2x1   lda     PX
        ldb     PY
        lbsr    Plot2
        inc     PX
        dec     TX
        bne     fr2x1
        inc     PY
        dec     TY
        bne     fr2y
fr2x    rts

DrawRect
        lda     Wd
        beq     drx
        lda     Ht
        beq     drx
        lda     RX
        sta     PX
        lda     Wd
        sta     TX
drtb    lda     PX
        ldb     RY
        lbsr    Plot2
        lda     PX
        ldb     RY
        addb    Ht
        decb
        lbsr    Plot2
        inc     PX
        dec     TX
        bne     drtb
        lda     RY
        sta     PY
        lda     Ht
        sta     TY
drsd    lda     RX
        ldb     PY
        lbsr    Plot2
        lda     RX
        adda    Wd
        deca
        ldb     PY
        lbsr    Plot2
        inc     PY
        dec     TY
        bne     drsd
drx     rts

***********************************************************************
* Text — 8x8 glyphs pre-defined; each char = 8 byte stores (not Plot2)
***********************************************************************
DrawStr
        sta     TX
        stb     TY
DrawStrCont
ds1     lda     ,x+
        beq     dsx
        sta     TmpCh
        pshs    x
        lda     TX
        ldb     TY
        lbsr    DrawChar
        puls    x
        lda     TX
        adda    #8
        sta     TX
        bra     ds1
dsx     rts

DrawNum
        clr     TmpH
dn1     cmpa    #10
        blo     dn2
        suba    #10
        inc     TmpH
        bra     dn1
dn2     pshs    a
        lda     TmpH
        adda    #'0
        sta     TmpCh
        lda     TX
        ldb     TY
        lbsr    DrawChar
        lda     TX
        adda    #8
        sta     TX
        puls    a
        adda    #'0
        sta     TmpCh
        lda     TX
        ldb     TY
        lbsr    DrawChar
        lda     TX
        adda    #8
        sta     TX
        rts

* A=x (use multiple of 8), B=y, TmpCh=ASCII
DrawChar
        sta     CX
        stb     CY
        lda     TmpCh
        cmpa    #'a
        blo     dcu
        cmpa    #'z
        bhi     dcu
        suba    #32
dcu     cmpa    #32
        blo     dcx
        cmpa    #91
        bhs     dcx
        suba    #32
        ldb     #8
        mul
        ldx     #Font8
        leax    d,x
        lda     CY
        ldb     #GBPL
        mul
        tfr     d,y
        lda     CX
        lsra
        lsra
        lsra
        leay    a,y
        leay    GFX,y
        ldb     #8
dc_blit lda     ,x+
        sta     ,y
        lda     #GBPL
        leay    a,y
        decb
        bne     dc_blit
dcx     rts

* 8x8 font ASCII 32-90, row-major, bit7=left. 8 bytes/glyph — blit as 8 STA.
Font8
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * space
        fcb     $18,$18,$18,$18,$18,$00,$18,$18  * !
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * "
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * #
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * $
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * %
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * &
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * '
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * (
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * )
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * *
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * +
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * ,
        fcb     $00,$00,$00,$7E,$00,$00,$00,$00  * -
        fcb     $00,$00,$00,$00,$00,$00,$18,$18  * .
        fcb     $03,$06,$0C,$18,$30,$60,$C0,$00  * /
        fcb     $7E,$C3,$C7,$CF,$DE,$E6,$C3,$7E  * 0
        fcb     $18,$38,$78,$18,$18,$18,$18,$7E  * 1
        fcb     $7E,$C3,$03,$06,$0C,$18,$30,$FF  * 2
        fcb     $7E,$C3,$03,$1E,$03,$03,$C3,$7E  * 3
        fcb     $0C,$1C,$3C,$6C,$CC,$FF,$0C,$0C  * 4
        fcb     $FF,$C0,$C0,$7E,$03,$03,$C3,$7E  * 5
        fcb     $3C,$60,$C0,$7E,$C3,$C3,$C3,$7E  * 6
        fcb     $FF,$03,$06,$0C,$18,$30,$30,$30  * 7
        fcb     $7E,$C3,$C3,$7E,$C3,$C3,$C3,$7E  * 8
        fcb     $7E,$C3,$C3,$7F,$03,$03,$06,$7C  * 9
        fcb     $00,$18,$18,$00,$00,$18,$18,$00  * :
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * ;
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * <
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * =
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * >
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * ?
        fcb     $00,$00,$00,$00,$00,$00,$00,$00  * @
        fcb     $3C,$66,$C3,$C3,$FF,$C3,$C3,$C3  * A
        fcb     $FE,$C3,$C3,$FE,$C3,$C3,$C3,$FE  * B
        fcb     $7E,$C3,$C0,$C0,$C0,$C0,$C3,$7E  * C
        fcb     $FC,$C6,$C3,$C3,$C3,$C3,$C6,$FC  * D
        fcb     $FF,$C0,$C0,$FC,$C0,$C0,$C0,$FF  * E
        fcb     $FF,$C0,$C0,$FC,$C0,$C0,$C0,$C0  * F
        fcb     $7E,$C3,$C0,$C0,$CF,$C3,$C3,$7E  * G
        fcb     $C3,$C3,$C3,$FF,$C3,$C3,$C3,$C3  * H
        fcb     $7E,$18,$18,$18,$18,$18,$18,$7E  * I
        fcb     $03,$03,$03,$03,$03,$C3,$C3,$7E  * J
        fcb     $C3,$C6,$CC,$F0,$CC,$C6,$C3,$C3  * K
        fcb     $C0,$C0,$C0,$C0,$C0,$C0,$C0,$FF  * L
        fcb     $C3,$E7,$FF,$DB,$C3,$C3,$C3,$C3  * M
        fcb     $C3,$E3,$F3,$DB,$CF,$C7,$C3,$C3  * N
        fcb     $7E,$C3,$C3,$C3,$C3,$C3,$C3,$7E  * O
        fcb     $FE,$C3,$C3,$FE,$C0,$C0,$C0,$C0  * P
        fcb     $7E,$C3,$C3,$C3,$DB,$CF,$C6,$7D  * Q
        fcb     $FE,$C3,$C3,$FE,$CC,$C6,$C3,$C3  * R
        fcb     $7E,$C3,$C0,$7E,$03,$03,$C3,$7E  * S
        fcb     $FF,$18,$18,$18,$18,$18,$18,$18  * T
        fcb     $C3,$C3,$C3,$C3,$C3,$C3,$C3,$7E  * U
        fcb     $C3,$C3,$C3,$C3,$C3,$66,$3C,$18  * V
        fcb     $C3,$C3,$C3,$C3,$DB,$FF,$E7,$C3  * W
        fcb     $C3,$C3,$66,$3C,$3C,$66,$C3,$C3  * X
        fcb     $C3,$C3,$66,$3C,$18,$18,$18,$18  * Y
        fcb     $FF,$03,$06,$0C,$18,$30,$60,$FF  * Z

***********************************************************************
* Keyboard — minimal POLCAT. Counters in B only (no BSS timer — a
* failed KTimer write caused infinite release-wait on some keys e.g. P).
***********************************************************************
POLCAT  equ     $A000

WaitKey
        andcc   #$EF            ; IRQs on for keyboard scan
        * drain any pending (bounded, register counter only)
        ldb     #40
wk_dr   jsr     [POLCAT]
        decb
        bne     wk_dr
        * wait for key (A != 0)
wk_wt   jsr     [POLCAT]
        anda    #$7F
        beq     wk_wt
        sta     KChar
        * drain/release (bounded — NEVER infinite)
        ldb     #80
wk_up   jsr     [POLCAT]
        decb
        bne     wk_up
        * small settle
        ldb     #0
wk_st   decb
        bne     wk_st
        lda     KChar
        anda    #$7F
        cmpa    #'a
        blo     wk_done
        cmpa    #'z
        bhi     wk_done
        suba    #32
wk_done rts

* Stored next to code so it is always in the LOADM image
KChar   fcb     0


* Sound / RNG
***********************************************************************
SoundInit
        lda     PIA1CRA
        ora     #$08
        sta     PIA1CRA
        lda     #$3C
        sta     PIA1CRB
        sta     PIA2CRB
        rts

Beep
        pshs    a,b,x
        tsta
        beq     b0
        cmpa    #1
        beq     b1
        ldb     #6
        ldx     #10
        bra     bg
b0      ldb     #3
        ldx     #14
        bra     bg
b1      ldb     #5
        ldx     #11
bg      lda     #$30
bi      sta     DAC
        eora    #$3F
        sta     DAC
        pshs    x
bd      leax    -1,x
        bne     bd
        puls    x
        deca
        bne     bi
        decb
        bne     bg
        puls    a,b,x
        rts

SeedRnd
        lda     $0113
        bne     srok
        lda     #$5A
srok    sta     Rnd
        rts
Rand
        lda     Rnd
        lsra
        bcc     rok
        eora    #$B4
rok     sta     Rnd
        rts
RandN
        sta     TmpN
        beq     rn1
rn0     lbsr    Rand
        lda     Rnd
rnm     cmpa    TmpN
        blo     rno
        suba    TmpN
        bra     rnm
rno     inca
        rts
rn1     lda     #1
        rts

* Strings
***********************************************************************
TTitle  fcn     "SEA BATTLE ML"
TSub    fcn     "PMODE4 DUAL BOARD"
TCtrl   fcn     "WASD MOVE  R ROTATE"
TCtrl2  fcn     "SPACE PUT  P AUTO"
TGo     fcn     "PRESS ANY KEY"
TPlace  fcn     "PLACE FLEET"
TShip   fcn     "SHIP"
THV     fcn     ""
TH      fcn     "HORIZ"
TV      fcn     "VERT"
THint   fcn     "WASD MOVE  P AUTO  SPC PUT"
TReady  fcn     "READY - KEY"
TComp   fcn     "COMPUTER PLACES..."
TYou    fcn     "YOUR FLEET"
TRad    fcn     "RADAR"
TStat   fcn     ""
TScE    fcn     "E:"
TScY    fcn     " Y:"
TMHit   fcn     "HIT!"
TMMiss  fcn     "MISS!"
TMSunk  fcn     "SUNK!"
TMAlr   fcn     "ALREADY"
TMComp  fcn     "COMPUTER"
TMComp2 fcn     "COMP DONE"
TWin    fcn     "YOU WIN!"
TLose   fcn     "YOU LOSE"
TmpCh   zmb     1

***********************************************************************
* Variables (in LOADM image)
***********************************************************************
PS      zmb     100
ES      zmb     100
RD      zmb     100
AK      zmb     100
SL      zmb     5
SR      zmb     5
PH      zmb     1
EH      zmb     1
Hunt    zmb     1
HR      zmb     1
HC      zmb     1
AR      zmb     1
AC      zmb     1
CurR    zmb     1
CurC    zmb     1
Horiz   zmb     1
ShipId  zmb     1
PlaceGrid zmb   1
Tries   zmb     1
TmpG    zmb     1
TmpR    zmb     1
TmpC    zmb     1
TmpL    zmb     1
TmpI    zmb     1
TmpN    zmb     1
TmpH    zmb     1
TmpCnt  zmb     1
TmpB    zmb     1
RR      zmb     1
CC      zmb     1
Rnd     zmb     1
BoardWhich zmb  1
BX0     zmb     1
BY0     zmb     1
X0      zmb     1
Y0      zmb     1
RX      zmb     1
RY      zmb     1
Wd      zmb     1
Ht      zmb     1
GType   zmb     1
CellVal zmb     1
PixX    zmb     1
PixY    zmb     1
PX      zmb     1
PY      zmb     1
TX      zmb     1
TY      zmb     1
CX      zmb     1
CY      zmb     1
ColMask zmb     1
ColN    zmb     1
RowBits zmb     1
RowN    zmb     1
HT      zmb     1
SID     zmb     1
CP      zmb     1

        end     START
