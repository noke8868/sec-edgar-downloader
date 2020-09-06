"""Provides a :class:`Downloader` class for downloading SEC EDGAR filings."""

import sys
from pathlib import Path
from typing import List, Optional

from ._constants import DEFAULT_AFTER_DATE, DEFAULT_BEFORE_DATE, SUPPORTED_FILINGS
from ._utils import download_filings, get_filing_urls_to_download, validate_date_format


class Downloader:
    """A :class:`Downloader` object.

    :param download_folder: relative or absolute path to download location.
        Defaults to the user's ``Downloads`` folder.

    Usage::

        >>> from sec_edgar_downloader import Downloader
        >>> dl = Downloader()
    """

    def __init__(self, download_folder: Optional[str] = None) -> None:
        """Constructor for the :class:`Downloader` class."""
        if download_folder is None:
            self.download_folder = Path.home().joinpath("Downloads")
        else:
            self.download_folder = Path(download_folder).expanduser().resolve()

    @property
    def supported_filings(self) -> List[str]:
        """Get a sorted list of all supported filings.

        :return: sorted list of all supported filings.

        Usage::

            >>> from sec_edgar_downloader import Downloader
            >>> dl = Downloader()
            >>> dl.supported_filings
            ['1', ..., '10-K', '10-KT', '10-Q', ..., '13F-HR', '13F-NT', ..., 'X-17A-5'']
        """
        return sorted(SUPPORTED_FILINGS)

    # TODO: add new arguments to docstring
    def get(
        self,
        filing_type: str,
        ticker_or_cik: str,
        num_filings_to_download: Optional[int] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        include_amends: bool = False,
        include_filing_details: bool = True,
    ) -> int:
        """Download filings and save them to disk.

        :param filing_type: type of filing to download.
        :param ticker_or_cik: ticker or CIK to download filings for.
        :param num_filings_to_download: number of filings to download.
            Defaults to all available filings.
        :param after_date: date of form YYYY-MM-DD in which to download filings after.
            Defaults to 2000-01-01, the earliest date supported by EDGAR full text search.
        :param before_date: date of form YYYY-MM-DD in which to download filings before.
            Defaults to today.
        :param include_amends: denotes whether or not to include filing amends (e.g. 8-K/A).
            Defaults to False.
        :param include_filing_details: denotes whether or not to include filing details
            (e.g. form 4 XML, 8-K HTML). Defaults to True.
        :return: number of filings downloaded.

        Usage::

            >>> from sec_edgar_downloader import Downloader
            >>> dl = Downloader()

            # Get all 8-K filings for Apple
            >>> dl.get("8-K", "AAPL")

            # Get all 8-K filings for Apple, including filing amends (8-K/A)
            >>> dl.get("8-K", "AAPL", include_amends=True)

            # Get all 8-K filings for Apple after January 1, 2017 and before March 25, 2017
            >>> dl.get("8-K", "AAPL", after_date="2017-01-01", before_date="2017-03-25")

            # Get the five most recent 10-K filings for Apple
            >>> dl.get("10-K", "AAPL", 5)

            # Get all 10-Q filings for Visa
            >>> dl.get("10-Q", "V")

            # Get all 13F-NT filings for the Vanguard Group
            >>> dl.get("13F-NT", "0000102909")

            # Get all 13F-HR filings for the Vanguard Group
            >>> dl.get("13F-HR", "0000102909")

            # Get all SC 13G filings for Apple
            >>> dl.get("SC 13G", "AAPL")

            # Get all SD filings for Apple
            >>> dl.get("SD", "AAPL")
        """
        if filing_type not in SUPPORTED_FILINGS:
            filing_options = ", ".join(sorted(SUPPORTED_FILINGS))
            raise ValueError(
                f"'{filing_type}' filings are not supported. "
                f"Please choose from the following: {filing_options}."
            )

        ticker_or_cik = str(ticker_or_cik).strip().upper().lstrip("0")

        # TODO: all filings should rely on after_date being 2000-01-01
        #  maxsize makes me uncomfortable
        if num_filings_to_download is None:
            # obtain all available filings, so we simply
            # need a large number to denote this
            num_filings_to_download = sys.maxsize
        else:
            num_filings_to_download = int(num_filings_to_download)
            if num_filings_to_download < 1:
                raise ValueError(
                    "Please enter a number greater than 1 "
                    "for the number of filings to download."
                )

        # SEC allows for filing searches from 2000 onwards
        if after_date is None:
            after_date = DEFAULT_AFTER_DATE
        else:
            after_date = str(after_date)
            validate_date_format(after_date)

            # TODO: test this!
            if after_date < DEFAULT_AFTER_DATE:
                raise ValueError(
                    "Filings cannot be downloaded prior to 2000. "
                    f"Please enter a date on or after {DEFAULT_AFTER_DATE}."
                )

        if before_date is None:
            before_date = DEFAULT_BEFORE_DATE
        else:
            before_date = str(before_date)
            validate_date_format(before_date)

        if after_date is not None and after_date > before_date:
            raise ValueError(
                "Invalid after_date and before_date. "
                "Please enter an after_date that is less than the before_date."
            )

        # TODO: add try/except for keyerror with link to issue reporting (SEC API may change)
        filings_to_fetch = get_filing_urls_to_download(
            filing_type,
            ticker_or_cik,
            num_filings_to_download,
            after_date,
            before_date,
            include_amends,
        )

        download_filings(
            self.download_folder,
            ticker_or_cik,
            filing_type,
            filings_to_fetch,
            include_filing_details,
        )

        return len(filings_to_fetch)
