***********************************************************************
* Full-screen PMODE 4 splash — raw 6144-byte frame at graphics page.
* Loaded by main.bas: LOADM"NAVAL" before LOADM"SEA" / EXEC.
* Page = $0E00 after PCLEAR4 / PMODE4,1 (same as PCLS target).
***********************************************************************
        org     $0E00

        includebin naval_pmode4.bin

        end
