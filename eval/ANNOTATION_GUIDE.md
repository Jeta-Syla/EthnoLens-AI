# Udhëzuesi i anotimit (50 receta)

## Qëllimi

Krijoni një standard reference njerëzor për të matur sa saktë sistemi gjen bimët dhe hollësitë e recetës. Anotoni vetëm atë që lexohet në pasazhin burimor. Mos përdorni njohuri moderne bimore për të plotësuar boshllëqe.

## Si të plotësohet CSV-ja

Përdorni `eval/annotations/<emri>.csv`. Çdo rresht përfaqëson një pasazh. Plotësoni kolonat `historical_name`, `plant_part`, `preparation`, `described_use` dhe `notes`.

- `historical_name`: emri i bimës saktësisht siç shfaqet në dorëshkrim, me drejtshkrimin historik. Një bimë për rresht. Nëse receta përmend dy bimë, kopjoni rreshtin dhe përdorni të njëjtin `passage_id` e `folio` për secilën.
- `plant_part`: pjesa e përmendur qartë (p.sh. leaf, root, seed). Shkruajeni anglisht, me shkronja të vogla dhe njëjës, që të përputhet me skemën. Lëreni bosh nëse nuk thuhet.
- `preparation`: fjalët e pasazhit që tregojnë përgatitjen, siç janë shkruar (p.sh. “sethe hem togidre”). Lëreni bosh nëse nuk përshkruhet.
- `described_use`: fjalët e pasazhit që tregojnë përdorimin historik. Mos e ktheni në këshillë ose pretendim mjekësor. Lëreni bosh nëse mungon.
- `notes`: paqartësi leximi, shtrirja e fjalëve të pasazhit, ose arsyeja kur një rresht mbetet i pazgjidhur. Mos vendosni identifikim modern këtu si fakt.

## Rregullat e vendimmarrjes

1. Lexoni gjithë tekstin nën folion përpara se të anotoni.
2. Përfshini vetëm bimët e identifikueshme nga teksti. Nëse teksti thotë vetëm “herbe” ose emri mungon/është i palexueshëm, mos shpikni emër bime; shpjegojeni te `notes`.
3. Ruani format e ndryshme historike siç janë; mos i bashkoni emrat e ngjashëm pa dëshmi të qartë.
4. Mos anotoni përbërësit që nuk janë bimë. Mos nxirrni pjesë, mënyrë përgatitjeje apo përdorim nga njohuri të përgjithshme.
5. Nëse një recetë ka disa bimë, krijoni një rresht për secilën bimë dhe përsëritni identifikuesit e pasazhit.
6. Për tekst të pasigurt, anotoni vetëm pjesën që mund ta mbështesni dhe shënoni pasigurinë te `notes`.

## Kontrolli para dorëzimit

- Numri i rreshtave mund të jetë më i madh se numri i recetave kur pasazhi ka disa bimë.
- Mos ndryshoni `passage_id` ose `folio` të dhënë.
- Kontrolloni që fushat bosh janë lënë bosh, pa `N/A`, hamendje ose placeholder.
- Ruani CSV-në në UTF-8 që shkronjat historike të mos humbin.

Anotuesit punojnë në mënyrë të pavarur. Mos shikoni rezultatet e nxjerrjes së modelit para se të përfundoni anotimin; kështu shmanget ndikimi në standardin e referencës.
