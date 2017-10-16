from time import sleep
from .base import FunctionalTest

class SiteCreationTests(FunctionalTest):

    def test_can_create_new_site(self):
        self.login()

        # There is a nav link to the creation page
        nav_links = self.browser.find_element_by_id("nav-links")
        nav_links = nav_links.find_elements_by_tag_name("a")
        self.assertEqual(nav_links[-2].text, "New Site")

        # They click it
        nav_links[-2].click()
        self.check_page("/sites/new/")
        self.check_title("New Zinc Site")
        self.check_h1("New Zinc Site")

        # They enter a zinc binding site and submit
        self.input_site("1TON", "A247", "A57", "A97", "A99")

        # They are on the page for the new site
        self.check_page("/sites/1TONA247/")
        self.check_title("Site 1TONA247")
        self.check_h1("Zinc Site: 1TONA247")

        # The new site looks fine
        self.check_site_page(
         "1TON", "3 June, 1987", "SUBMAXILLARY GLAND",
         ["A57", "A97", "A99"], ["HIS"] * 3
        )


    def test_can_create_site_in_existing_pdb(self):
        self.login()

        # There is a nav link to the creation page
        nav_links = self.browser.find_element_by_id("nav-links")
        nav_links = nav_links.find_elements_by_tag_name("a")
        self.assertEqual(nav_links[-2].text, "New Site")
        nav_links[-2].click()

        # They enter a zinc binding site and submit
        self.input_site("5O8H", "A502", "A38", "A62", "A153")

        # They are on the page for the new site
        self.check_page("/sites/5O8HA502/")
        self.check_title("Site 5O8HA502")
        self.check_h1("Zinc Site: 5O8HA502")

        # The new site looks fine
        self.check_site_page(
         "5O8H", "11 October, 2017", "CRYSTAL STRUCTURE OF R. RUBER",
         ["A38", "A62", "A153"], ["CYS", "HIS", "ASP"]
        )
