# Existing judges

Before we wrote the judges in this repository, other people had already published judges for most Hash Code problems.
This file lists them.

We analyzed each of these judges before we wrote our own. We read the code to learn how it reads the input file and
the output file, which rules it checks and how it computes the score. We used what we found to choose the edge cases our
judges must handle. Where a judge or its repository came with published output files and scores, we used them to
cross-check our scores.

None of these judges is part of this repository. Our judges do not import or copy code from them.

Many of the existing judges compute the score correctly for a valid output file, but check few of the rules. Common gaps
are a missing range check on IDs, duplicate IDs that pass, an error that is only logged while the judge still prints a
score, and lines after the last expected line that the judge ignores.

| Year | Round | Problem | Our judge | Existing judges |
| ---- | ----- | ------- | --------- | --------------- |
| 2017 | Practice Round | Pizza | [pizza](pizza/) | [renuo/hashcode2017-jamp-pizza](https://github.com/renuo/hashcode2017-jamp-pizza/blob/master/solution_validator.rb), [uran-lajci/pizza-validator](https://github.com/uran-lajci/pizza-validator) |
| 2020 | Practice Round | More pizza | [more_pizza](more_pizza/) | [sbrodehl/Hashcode2k20](https://github.com/sbrodehl/Hashcode2k20/blob/master/Practice%20Round/solver/scoring.py) |
| 2021 | Practice Round | Even more pizza | [even_more_pizza](even_more_pizza/) | [sbrodehl/hashcode2021](https://github.com/sbrodehl/hashcode2021/blob/main/Practice%20Round/solver/scoring.py) |
| 2022 | Practice Round | One pizza | [one_pizza](one_pizza/) | [sbrodehl/hashcode2022](https://github.com/sbrodehl/hashcode2022/blob/main/Qualification%20Round/solver/scoring.py) |
| 2015 | Qualification Round | Optimize a data center | [optimize_a_data_center](optimize_a_data_center/) | [jorpilo/HashCode2015-Checker](https://github.com/jorpilo/HashCode2015-Checker) |
| 2016 | Qualification Round | Delivery | [delivery](delivery/) | [vitowalteranelli/Google-HashCode-Playground](https://github.com/vitowalteranelli/Google-HashCode-Playground/tree/master/hashcode2016_qualification) |
| 2017 | Qualification Round | Streaming videos | [streaming_videos](streaming_videos/) | [vitowalteranelli/Google-HashCode-Playground](https://github.com/vitowalteranelli/Google-HashCode-Playground/tree/master/hashcode2017_qualification) |
| 2018 | Qualification Round | Self-driving rides | [self_driving_rides](self_driving_rides/) | [vitowalteranelli/Google-HashCode-Playground](https://github.com/vitowalteranelli/Google-HashCode-Playground/tree/master/hashcode2018_qualification), [PicoJr/2018-hashcode-score](https://github.com/PicoJr/2018-hashcode-score) |
| 2019 | Qualification Round | Photo slideshow | [photo_slideshow](photo_slideshow/) | [PicoJr/2019-hashcode-score](https://github.com/PicoJr/2019-hashcode-score) |
| 2020 | Qualification Round | Book scanning | [book_scanning](book_scanning/) | [PellegattaSimone/Hash-Code-2020-Score-Calculator](https://github.com/PellegattaSimone/Hash-Code-2020-Score-Calculator), [PicoJr/2020-hashcode-score](https://github.com/PicoJr/2020-hashcode-score) |
| 2021 | Qualification Round | Traffic signaling | [traffic_signaling](traffic_signaling/) | [KristofHolecz/hash-code-2021-traffic-signaling-insights-reporter](https://github.com/KristofHolecz/hash-code-2021-traffic-signaling-insights-reporter), [PicoJr/google-hashcode-score-2021](https://github.com/PicoJr/google-hashcode-score-2021) |
| 2022 | Qualification Round | Mentorship and teamwork | [mentorship_and_teamwork](mentorship_and_teamwork/) | [KristofHolecz/hash-code-2022-mentorship-and-teamwork-insights-reporter](https://github.com/KristofHolecz/hash-code-2022-mentorship-and-teamwork-insights-reporter), [PicoJr/google-hashcode-score-2022](https://github.com/PicoJr/google-hashcode-score-2022) |
| 2014 | Final Round | Street View routing | [street_view_routing](street_view_routing/) | [gdalle/GoogleHashCode2014.jl](https://github.com/gdalle/GoogleHashCode2014.jl) |
| 2015 | Final Round | Loon | [loon](loon/) | [Dewep/HashCode2015-finalround-extended](https://github.com/Dewep/HashCode2015-finalround-extended) |
| 2016 | Final Round | Satellites | [satellites](satellites/) | [vitowalteranelli/Google-HashCode-Playground](https://github.com/vitowalteranelli/Google-HashCode-Playground/tree/master/hashcode2016_final_task) |
| 2017 | Final Round | Router placement | [router_placement](router_placement/) | [uran-lajci/router-placement-validator](https://github.com/uran-lajci/router-placement-validator), [vitowalteranelli/Google-HashCode-Playground](https://github.com/vitowalteranelli/Google-HashCode-Playground/tree/master/hashcode2017_final_task) |
| 2018 | Final Round | City plan | [city_plan](city_plan/) | [mihai-bontea/Google-Hash-Code-2018-Final-Round](https://github.com/mihai-bontea/Google-Hash-Code-2018-Final-Round) |
| 2019 | Final Round | Compiling Google | [compiling_google](compiling_google/) | [LarsAstrom/Hashcode-final-2019](https://github.com/LarsAstrom/Hashcode-final-2019) |
| 2020 | Final Round | Assembling smartphones | [assembling_smartphones](assembling_smartphones/) | [Nanored4498/HashCode2022](https://github.com/Nanored4498/HashCode2022), [uran-lajci/google-hash-code-assembling-smartphones](https://github.com/uran-lajci/google-hash-code-assembling-smartphones) |
| 2021 | Final Round | Software engineering at scale | [software_engineering_at_scale](software_engineering_at_scale/) | [AlexeyZhuravlev/hashcode-practice-2021-finals](https://github.com/AlexeyZhuravlev/hashcode-practice-2021-finals) |
| 2022 | Final Round | Santa tracker | Not written yet | None found |
