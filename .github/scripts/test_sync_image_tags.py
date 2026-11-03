import unittest
from unittest.mock import patch

import sync_image_tags as sync


def release(version, commit="1206e6b", pushed="2026-11-01T00:00:00Z", digest="a"):
    return {
        "name": f"{version}-{commit}",
        "digest": "sha256:" + digest * 64,
        "tag_last_pushed": pushed,
        "tag_status": "active",
        "images": [{"os": "linux", "architecture": arch, "status": "active"}
                   for arch in ("amd64", "arm64")],
    }


class AliasTests(unittest.TestCase):
    def test_old_series_patch_cannot_replace_latest(self):
        old = release("1.26.11", pushed="2026-11-03T00:00:00Z")
        new = release("1.27.3", digest="b")
        for tags in ([old, new], [new, old]):
            aliases = sync.select_aliases(tags)
            self.assertEqual(aliases["latest"], new)
            self.assertEqual(aliases["1.26"], old)
            self.assertEqual(aliases["1.27"], new)

    def test_numeric_order_and_equal_go_version(self):
        newest = release("1.26.10", commit="aaaaaaa", pushed="2026-11-03T00:00:00.1691Z")
        tags = [release("1.26.9"), newest, release("1.26.10", commit="bbbbbbb")]
        self.assertEqual(sync.select_aliases(tags)["latest"], newest)
        self.assertEqual(sync.select_aliases(list(reversed(tags)))["latest"], newest)

    def test_ignore_floating_prerelease_and_incomplete_tags(self):
        good = release("1.26.10")
        incomplete = release("1.28.1")
        incomplete["images"].pop()
        inactive = release("1.29.1")
        inactive["tag_status"] = "inactive"
        bad_names = [dict(good, name=name) for name in ("latest", "1.26", "1.28.0-rc1", "sha256-abc")]
        self.assertEqual(sync.select_aliases([good, incomplete, inactive, *bad_names])["latest"], good)

    def test_empty_or_invalid_digest_fails(self):
        with self.assertRaises(ValueError):
            sync.select_aliases([])
        with self.assertRaises(ValueError):
            sync.select_aliases([dict(release("1.26.10"), digest="invalid")])

    @patch.object(sync, "docker")
    def test_preview_does_not_call_docker(self, docker):
        sync.sync("test/image", [release("1.26.10")])
        docker.assert_not_called()

    @patch.object(sync, "docker")
    def test_unknown_existing_alias_aborts_without_writes(self, docker):
        with self.assertRaises(ValueError):
            sync.sync("test/image", [release("1.26.10"), {"name": "latest", "digest": "unknown"}], True)
        docker.assert_not_called()

    @patch.object(sync, "docker")
    def test_apply_copies_digest_and_verifies(self, docker):
        tag = release("1.26.10")
        docker.side_effect = [
            '{"manifests":[{"platform":{"os":"linux","architecture":"amd64"}},'
            '{"platform":{"os":"linux","architecture":"arm64"}}]}',
            "", tag["digest"], "", tag["digest"],
        ]
        sync.sync("test/image", [tag], True)
        creates = [call for call in docker.call_args_list if call.args[0] == "create"]
        self.assertEqual(len(creates), 2)
        self.assertTrue(all(call.args[-1] == "test/image@" + tag["digest"] for call in creates))

    @patch.object(sync, "docker", return_value='{"manifests":[]}')
    def test_incomplete_source_aborts_before_any_write(self, docker):
        with self.assertRaises(ValueError):
            sync.sync("test/image", [release("1.26.10")], True)
        self.assertEqual(docker.call_count, 1)

    @patch.object(sync.urllib.request, "urlopen")
    def test_paginated_listing(self, urlopen):
        import io
        urlopen.side_effect = [
            io.StringIO('{"results":[{"name":"a"}],"next":"https://hub.docker.com/v2/page2"}'),
            io.StringIO('{"results":[{"name":"b"}],"next":null}'),
        ]
        self.assertEqual(sync.list_tags("test/image"), [{"name": "a"}, {"name": "b"}])


if __name__ == "__main__":
    unittest.main()
