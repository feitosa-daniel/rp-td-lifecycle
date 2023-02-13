# The Lifecycle of Technical Debt that Manifests in both Source Code and Issue Trackers

## Replication Package

##### Authors: Jie Tan, Daniel Feitosa, Paris Avgeriou

> NOTE: **Long-term storage** 
> This is a temporary repository for review. If the submission is accepted, we will upload its content to an archival repository that guarantees long-time storage and update the manuscript with the DOI.

## Description of this study

Although Technical Debt (TD) has increasingly gained attention in recent years, most studies exploring TD are based on a single source (e.g., source code, code comments or issue trackers).
Investigating information combined from different sources may yield insight that is more than the sum of its parts. In particular, we argue that exploring how TD items are managed in both issue trackers and software repositories (including source code and commit messages) can shed some light on what happens between the commits that incur TD and those that pay it back. 
To this end, we randomly selected 3,000 issues from the trackers of five projects, manually analyzed 300 issues that contained TD information, and identified and investigated the lifecycle of 312 TD items. 
The results indicate that most of the TD items marked as resolved in issue trackers are also paid back in source code, although many are not discussed after being identified in the issue tracker. Test Debt items are the least likely to be paid back in source code. We also learned that although TD items may be resolved a few days after being identified, it often takes a long time to be identified (around one year). In general, time is reduced if the same developer is involved in consecutive moments (i.e., introduction, identification, repayment decision-making and remediation), but whether the developer who paid back the item is involved in discussing the TD item does not seem to affect how quickly it is resolved.
Investigating how developers manage TD across both source code repositories and issue trackers can lead to a more comprehensive oversight of this activity and support efforts to shorten the lifecycle of undesirable debt. 

## Contents

### Data

- `data/data-collection-step1-3000-random-issues.csv`\
    A CSV containing a list of the 3,000 issues from the trackers of five Apache open-source projects.
- `data/data-collection-step2-300-random-issues.csv`\
    A CSV containing the issue section of the 3,000 issues. Each section contains its text and the TD classification of the section (i.e., non-debt or one of eight types of debt followed with a subtype).
- `data/data-collection-step3-issue-sections-with-related-commits.csv`\
    A version of the previous CSV added with the related commits, i.e., that mention the respective issue in the commit message or that is in the same PR as one such commit.
- `data/dataset.csv`\
    The complete dataset of this study. It is a version of the previous CSV populated with all information necessary to answer the research questions. Issues that have not been analyzed are still in the dataset but do not contain information for any of the detail columns.
- `data/rq*.csv`\
    A data subsets derived from `dataset.csv` with the data filtered to answer a particular research question.

### Figures

The figures used in the paper can be found in the folder `figs/`. The figures are generated using the notebook `scripts/data-analysis.ipynb`.

### Scripts

- `Dockerfile`, `docker-compose.yaml`, `env.yaml`\
    Files to build and start a Docker container with a JupyterLab instance and all necessary dependencies (see `env.yaml`).

- `scripts/data-analysis.ipynb`\
    Jupyter notebook that contains all analysis (including statistics and figures) reported in the paper.

- Running scripts (via JupyterLab):
    1. Install [Docker Engine](https://docs.docker.com/engine/install/)
    2. In the terminal/cmd
       1. Navigate to this folder
       2. Run `docker compose up`
    3. In your web browser, navigate to https://localhost:8888

## Paper

Latest version available on [arXiv](https://arxiv.org/abs/xxxxx)

If you publish a paper where this dataset helps your research, we encourage you to cite the following paper in your publication:

```

```


## Licenses

The software in this repository is licensed under the [MIT License](LICENSE).

The data compiled in this repository is licensed under the [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0) License.

